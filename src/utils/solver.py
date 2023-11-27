from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar
from typing import List, Dict, Tuple, Any
from src.models.solver_model import Room, ActivityRoom, ActivityConditionOption, ActivityConditionOptionType, ConditionScope, Condition, Assessment, Activity, RoomConditionOption, RoomConditionOptionType, RoomType
from datetime import timedelta
import collections

class Solver:
    """A class for solving the scheduling problem of the assessments.
    
    Assumptions:
    - The data received is already structured and validated
    """
        
    def __init__(self, time_start: timedelta, time_end: timedelta, time_max_interval: timedelta, time_max_gap: timedelta, time_transfer: timedelta, num_floors: int, num_doctors: int, simultaneous_transfers: bool) -> None:
        """Initializer for the solver

        Args:
            time_start (timedelta): the start time of the schedule
            time_end (timedelta): the end time of the schedule
            time_max_gap (timedelta): the maximum gap between activities
            time_transfer (timedelta): the time needed for transferring between activities
            num_floors (int): the names of the assessments
        """
        self.__time_start = time_start
        self.__time_end = time_end
        self.__time_max_interval = int(time_max_interval.total_seconds() // 60)
        self.__time_max_gap = int(time_max_gap.total_seconds() // 60)
        self.__time_transfer = int(time_transfer.total_seconds() // 60)
        
        self.__num_floors = num_floors
        
        self.__simultaneous_transfers = simultaneous_transfers
        
        self.__horizon = int((time_end - time_start).total_seconds() // 60)
        
        self.__activity_type = collections.namedtuple('task_type', 'duration id room_id room_floor')
        
        self.__model = cp_model.CpModel()
        self.__assessments = None
        self.__schedules: List[List[List[self.__activity_type]]] = []
        self.__conditions_per_room = collections.defaultdict(list)
        self.__conditions_per_assessment: Dict[int, List[Condition]] = collections.defaultdict(list)
        
        self.__clients_per_assessment = collections.defaultdict(list)
        self.__time_interval_vars_per_room = collections.defaultdict(list)
        self.__time_interval_vars_per_client = collections.defaultdict(list)
        self.__activity_bool_vars = collections.defaultdict(list)
        self.__client_activity_rooms = collections.defaultdict(list)
        self.__last_activity_end_time_int_vars = []
        
        self.__activity_index_floor_bool_vars = dict()
        self.__activity_index_time_interval_vars = dict()
        self.__activity_index_start_time_int_vars = dict()
        self.__activity_index_end_time_int_vars = dict()
        self.__activity_index_room_bool_vars = dict()
        
        self.__activity_room_bool_vars = collections.defaultdict(list)
        self.__activity_floor_bool_vars = collections.defaultdict(list)
        self.__activity_time_interval_vars = collections.defaultdict(list)
        self.__activity_start_time_int_vars = collections.defaultdict(list)
        self.__activity_end_time_int_vars = collections.defaultdict(list)

        self.__room_floor_bool_vars: Dict[Tuple[int, int, int], IntVar] = dict()
        self.__transfer_time_interval_vars = dict()
        self.__transfer_start_time_int_vars = dict()
        self.__transfer_end_time_int_vars = dict()
    
    def __get_assessment_by_client_id(self, client_id: int) -> Assessment:
        """Helper function for getting the assessment of a client

        Args:
            client_id (int): the id of the client

        Returns:
            Assessment: the assessment of the client
        """
        for assessment in self.__assessments:
            if client_id in self.__clients_per_assessment[assessment.id]:
                return assessment
        return None
    
    def __define_objective(self):
        """Helper function for defining the objective of the solver
        """
        assert len(self.__last_activity_end_time_int_vars) == sum([_assessment.quantity for _assessment in self.__assessments]), 'Invalid number of last activities'
        
        makespan = self.__model.NewIntVar(0, self.__horizon, 'makespan')
        self.__model.AddMaxEquality(makespan, self.__last_activity_end_time_int_vars)
        self.__model.Minimize(makespan)
    
    def __initialize_variables(self):
        """Helper function for initializing the variables of the solver. It must be ran prior to the definition of the variables.
        """
        previous_assessment_quantity = 0
        for assessment in self.__assessments:
            activities = []
            for activity in assessment.activities:
                for activity_room in activity.rooms:
                    activities.append(
                        self.__activity_type(activity_room.duration, activity.id, activity_room.room.id, activity_room.room.floor)
                    )
                    for room_condition in activity_room.room.conditions:
                        self.__conditions_per_room[activity_room.room.id].append(room_condition)
                for condition in activity.conditions:
                    self.__conditions_per_assessment[assessment.id].append(condition)
            schedule = [activities] * len(assessment.activities)
            self.__schedules.extend(
                [schedule] * assessment.quantity
            )
            self.__clients_per_assessment[assessment.id].extend(list(range(previous_assessment_quantity, previous_assessment_quantity + assessment.quantity)))
            previous_assessment_quantity += assessment.quantity
    
    def __define_variables(self):
        """Helper function for defining the variables of the solver
        """
        assert self.__schedules is not None, 'Invalid schedules'
        
        for client_id, schedule in enumerate(self.__schedules):
            previous_end = None
            for activity_index, activities in enumerate(schedule):
                min_duration = activities[0].duration
                max_duration = activities[0].duration
                
                for activity in activities[1:]:
                    min_duration = min(min_duration, activity.duration)
                    max_duration = max(max_duration, activity.duration)
                
                suffix = f'_c{client_id}_a{activity_index}'
                start = self.__model.NewIntVar(0, self.__horizon, f'start{suffix}')
                duration = self.__model.NewIntVar(min_duration, max_duration, f'duration{suffix}')
                end = self.__model.NewIntVar(0, self.__horizon, f'end{suffix}')
                interval = self.__model.NewIntervalVar(start, duration, end, f'interval{suffix}')
                floor = self.__model.NewIntVar(1, self.__num_floors, f'floor{suffix}')
                
                self.__activity_index_start_time_int_vars[(client_id, activity_index)] = start
                self.__activity_index_end_time_int_vars[(client_id, activity_index)] = end
                self.__activity_index_time_interval_vars[(client_id, activity_index)] = interval
                self.__activity_index_floor_bool_vars[(client_id, activity_index)] = floor
                
                if previous_end is not None:
                    self.__model.Add(start >= previous_end)
                
                previous_end = end
                  
                if len(activities) > 1:
                    current_activities = []
                    for sub_activity_index, activity in enumerate(activities):
                        other_suffix = f'_c{client_id}_a{activity_index}_r{activity.room_id}'
                        current_start = self.__model.NewIntVar(0, self.__horizon, f'start{other_suffix}')
                        current_duration = activity.duration
                        current_end = self.__model.NewIntVar(0, self.__horizon, f'end{other_suffix}')
                        current_activity = self.__model.NewBoolVar(f'room{other_suffix}')
                        current_interval = self.__model.NewOptionalIntervalVar(current_start, current_duration, current_end, current_activity, f'interval{other_suffix}')
                        current_floor = self.__model.NewIntVar(0, self.__num_floors, f'floor{other_suffix}')
                        
                        current_activities.append(current_activity)
                        
                        self.__time_interval_vars_per_room[activity.room_id].append(current_interval)
                        self.__time_interval_vars_per_client[client_id].append(current_interval)
                        
                        self.__activity_index_room_bool_vars[(client_id, activity.id, activity_index, activity.room_id)] = current_activity
                        self.__activity_bool_vars[(client_id, activity.id)].append(current_activity)
                        
                        self.__model.Add(start == current_start).OnlyEnforceIf(current_activity)
                        self.__model.Add(duration == current_duration).OnlyEnforceIf(current_activity)
                        self.__model.Add(end == current_end).OnlyEnforceIf(current_activity)
                        self.__model.Add(current_floor == activity.room_floor).OnlyEnforceIf(current_activity)
                        self.__model.Add(floor == current_floor).OnlyEnforceIf(current_activity)
                        
                        self.__activity_start_time_int_vars[(client_id, activity.id)].append(current_start)
                        self.__activity_end_time_int_vars[(client_id, activity.id)].append(current_end)
                        self.__activity_time_interval_vars[(client_id, activity.id)].append(current_interval)
                        self.__activity_floor_bool_vars[(client_id, activity.id)].append(current_floor)
                        self.__activity_room_bool_vars[(activity.room_id, activity_index, activity.id)].append(current_activity)
                        self.__client_activity_rooms[(client_id, activity.id, activity.room_id)].append(current_activity)
                        
                    self.__model.AddExactlyOne(current_activities)
                else:
                    self.__model.Add(floor == activities[0].room_floor)
                    
                    self.__activity_start_time_int_vars[(client_id, activities[0].id)].append(start)
                    self.__activity_end_time_int_vars[(client_id, activities[0].id)].append(end)
                    self.__activity_time_interval_vars[(client_id, activities[0].id)].append(interval)
                    self.__activity_floor_bool_vars[(client_id, activities[0].id)].append(floor)
                    self.__activity_room_bool_vars[(activities[0].room_id, 0, activities[0].id)].append(self.__model.NewConstant(1))
                    
                    self.__time_interval_vars_per_room[activities[0].room_id].append(interval)
                    self.__time_interval_vars_per_client[client_id].append(interval)
                    
                    self.__activity_index_room_bool_vars[(client_id, activities[0].id, activity_index, activities[0].room_id)] = self.__model.NewConstant(1)
                    self.__client_activity_rooms[(client_id, activities[0].id, activities[0].room_id)].append(self.__model.NewConstant(1))
                    self.__activity_bool_vars[(client_id,  activities[0].id)].append(self.__model.NewConstant(1))                    
                
            self.__last_activity_end_time_int_vars.append(previous_end)
    
    def __apply_general_constraints(self):
        """Helper function for applying all general constraints of the solver namely:
        
        - Generate Optimal before Ultimate
        - Transfers can either be simultaneous or not
        - No overlap between activities
        - All activities must be performed
        - All times must be divisible by 5
        """
        if not self.__simultaneous_transfers:
            self.__model.AddNoOverlap(self.__transfer_time_interval_vars.values())
        
        self.__apply_no_overlap_activity_constraint(201)
        self.__apply_simultaneous_transfers_constraint(self.__simultaneous_transfers)
        
        for client_id, schedule in enumerate(self.__schedules):
            self.__apply_transfer_constraint(client_id, schedule)
            self.__apply_max_gap_constraint(client_id, schedule)
            self.__apply_no_overlap_client_constraint(client_id)
            
            assessment = self.__get_assessment_by_client_id(client_id)
            for activity in assessment.activities:
                self.__model.AddExactlyOne(self.__activity_bool_vars[(client_id, activity.id)])
                        
            for activity_index, _ in enumerate(self.__schedules[client_id]):
                self.__model.AddModuloEquality(0, self.__activity_index_start_time_int_vars[(client_id, activity_index)], self.__time_max_interval)
                self.__model.AddModuloEquality(0, self.__activity_index_end_time_int_vars[(client_id, activity_index)], self.__time_max_interval)
    
    def __apply_no_overlap_client_constraint(self, client_id: int):
        """Helper function for applying the no overlap constraint at the client level of the solver.
        """
        self.__model.AddNoOverlap(self.__time_interval_vars_per_client[client_id])
    
    def __apply_no_overlap_activity_constraint(self, activity_id: int):
        """Helper function for applying the no overlap constraint at the activity level of the solver.
        """
        matching_intervals = [i for k, v in self.__activity_time_interval_vars.items() for i in v if k[1] == activity_id]
        self.__model.AddNoOverlap(matching_intervals)
    
    def __apply_assessment_precedence_constraint(self, assessment_id: int, other_assessment_id: int, generate: bool = True):
        pass
    
    def __apply_simultaneous_transfers_constraint(self, generate: bool = True):
        """Helper function for applying allowing simultaneous transfers constraint of the solver.
        """
        if not generate:
            self.__model.AddNoOverlap(self.__transfer_time_interval_vars.values())
    
    def __apply_max_gap_constraint(self, client_id: int, schedule: List[List[Any]]):
        """Helper function for applying the max gap constraint of the solver.
        """
        for activity_index, _ in enumerate(schedule):
            other_activity_index = activity_index + 1
            if other_activity_index < len(schedule):
                self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] - self.__activity_index_end_time_int_vars[(client_id, activity_index)] <= self.__time_max_gap).OnlyEnforceIf(self.__room_floor_bool_vars[(client_id, activity_index, other_activity_index)].Not())
    
    def __apply_transfer_constraint(self, client_id: int, schedule: List[List[Any]]):
        """Helper function for applying the transfer constraint of the solver.
        """
        for activity_index, _ in enumerate(schedule):
            other_activity_index = activity_index + 1
            if other_activity_index < len(schedule):
                suffix = f'_trf_c{client_id}_a{activity_index}_a{other_activity_index}'
                start = self.__model.NewIntVar(0, self.__horizon, f'start{suffix}')
                duration = self.__time_transfer
                end = self.__model.NewIntVar(0, self.__horizon, f'end{suffix}')
                floor = self.__model.NewBoolVar(f'floor{suffix}')
                interval = self.__model.NewOptionalIntervalVar(start, duration, end, floor, f'interval{suffix}')
                
                self.__room_floor_bool_vars[(client_id, activity_index, other_activity_index)] = floor
                
                self.__model.AddModuloEquality(0, start, self.__time_max_interval)
                self.__model.AddModuloEquality(0, end, self.__time_max_interval)
                
                self.__model.Add(self.__activity_index_floor_bool_vars[(client_id, activity_index)] != self.__activity_index_floor_bool_vars[(client_id, other_activity_index)]).OnlyEnforceIf(floor)
                self.__model.Add(self.__activity_index_floor_bool_vars[(client_id, activity_index)] == self.__activity_index_floor_bool_vars[(client_id, other_activity_index)]).OnlyEnforceIf(floor.Not())
                
                self.__model.Add(start == self.__activity_index_end_time_int_vars[(client_id, activity_index)]).OnlyEnforceIf(floor)
                self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] == end).OnlyEnforceIf(floor)
                
                self.__time_interval_vars_per_client[client_id].append(interval)
                self.__transfer_start_time_int_vars[(client_id, activity_index, other_activity_index)] = start
                self.__transfer_end_time_int_vars[(client_id, activity_index, other_activity_index)] = end
                self.__transfer_time_interval_vars[(client_id, activity_index, other_activity_index)] = interval
    
    def __apply_activity_constraints(self):
        """Helper function for applying all activity constraints of the solver namely:

        - Before constraints
        - After constraints
        - Right after activity constraint
        - Right before activity constraint
        - Between constraints
        - Within after activity constraint
        - Within before activity constraint
        """
        for client_id, _ in enumerate(self.__schedules):
            for condition in self.__conditions_per_assessment[self.__get_assessment_by_client_id(client_id).id]:
                if condition.scope != ConditionScope.ACTIVITY.value:
                    raise ValueError('Invalid condition scope for activity constraint')
                
                if condition.option == ActivityConditionOption.BEFORE.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_before_activity_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.TIME.value:
                        self.__apply_before_time_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.ORDER.value:
                        self.__apply_before_order_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for before activity constraint')
                elif condition.option == ActivityConditionOption.AFTER.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_after_activity_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.TIME.value:
                        self.__apply_after_time_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.ORDER.value:
                        self.__apply_after_order_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for after activity constraint')
                elif condition.option == ActivityConditionOption.RIGHT_AFTER.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_right_after_activity_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for right after activity constraint')
                elif condition.option == ActivityConditionOption.RIGHT_BEFORE.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_right_before_activity_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for right before activity constraint')
                elif condition.option == ActivityConditionOption.BETWEEN.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_between_activities_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.TIME.value:
                        self.__apply_between_times_constraint(client_id, **condition.args)
                    elif condition.option_type == ActivityConditionOptionType.ORDER.value:
                        self.__apply_between_orders_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for between constraint')
                elif condition.option == ActivityConditionOption.WITHIN_AFTER.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_within_after_activity_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for within after activity constraint')
                elif condition.option == ActivityConditionOption.WITHIN_BEFORE.value:
                    if condition.option_type == ActivityConditionOptionType.ACTIVITY.value:
                        self.__apply_within_before_activity_constraint(client_id, **condition.args)
                    else:
                        raise ValueError('Invalid condition option type for within before activity constraint')
                elif condition.option == ActivityConditionOption.IN_FIXED_ORDER_AS.value:
                    if condition.option_type == ActivityConditionOptionType.ORDER.value:
                        self.__apply_order_constraint(client_id,**condition.args)
                    else:
                        raise ValueError('Invalid condition option type for in fixed order as constraint')
                else:
                    raise ValueError('Invalid condition option')
        
    # Activity Conditions
    def __apply_before_activity_constraint(self, client_id: int, activity_id: int, other_activity_id: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be before another activity; end time of activity <= start time of another activity. 

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            before_activity_id (int): the id of the other acti vity
            generate (bool): whether to generate or avoid generating the constraint
        """
        for start in self.__activity_start_time_int_vars[(client_id, other_activity_id)]:
            for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
                if generate:
                    self.__model.Add(end <= start)
        
    def __apply_before_time_constraint(self, client_id: int, activity_id: int, time_before: timedelta, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be before a certain time; end time of activity <= time_before.

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            time_before (int): the maximum time limit for the end of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        time_before = int((time_before - self.__time_start).total_seconds() // 60)
        for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(end <= time_before)           
    
    def __apply_before_order_constraint(self, client_id, activity_id: int, order: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be before a certain order; end time of activity <= start time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        self.__apply_order_constraint(client_id, activity_id, order - 1, generate)
    
    def __apply_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be after another activity; start time of activity >= end time of another activity.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            for end in self.__activity_end_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(start >= end)
    
    def __apply_after_time_constraint(self, client_id, activity_id: int, time_after: timedelta, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be after a certain time; start time of activity >= time_after.

        Args:
            activity_id (int): the id of the activity
            time_after (int): the minimum time limit for the start of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        time_after = int((time_after - self.__time_start).total_seconds() // 60)
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(start >= time_after) 
    
    def __apply_after_order_constraint(self, client_id, activity_id: int, order: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be after a certain order; start time of activity >= end time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        self.__apply_order_constraint(client_id, activity_id, order + 1, generate)
    
    def __apply_right_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be right after another activity; start time of activity >= end time of another activity && start time of activity - end time of another activity <= time_max_gap.

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_max_gap (int): the maximum time gap between the two activities
            generate (bool): whether to generate or avoid generating the constraint
        """
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            for end in self.__activity_end_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(start >= end)
                    self.__model.Add(start - end <= self.__time_max_gap)
    
    def __apply_right_before_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be right before another activity; end time of activity <= start time of another activity && start time of another activity - end time of activity <= time_max_gap.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_max_gap (int): the maximum time gap between the two activities
            generate (bool): whether to generate or avoid generating the constraint
        """
        for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
            for start in self.__activity_start_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(end <= start)
                    self.__model.Add(start - end <= self.__time_max_gap)
    
    def __apply_between_activities_constraint(self, client_id, activity_id: int, other_activity_id_before: int, other_activity_id_after: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two other activities; start time of activity >= end time of another activity before && end time of activity <= start time of another activity after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id_before (int): the id of the other activity before
            other_activity_id_after (int): the id of the other activity after
            generate (bool): whether to generate or avoid generating the constraint
        """
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            for end in self.__activity_end_time_int_vars[(client_id, other_activity_id_before)]:
                if generate:
                    self.__model.Add(start >= end)

        for start in self.__activity_start_time_int_vars[(client_id, other_activity_id_after)]:
            for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
                if generate:
                    self.__model.Add(end <= start)
    
    def __apply_between_times_constraint(self, client_id, activity_id: int, time_before: timedelta, time_after: timedelta, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two times; start time of activity >= time_before && end time of activity <= time_after.

        Args:
            activity_id (int): the id of the activity
            time_before (int): the minimum time limit for the start of the activity
            time_after (int): the maximum time limit for the end of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        time_before = int((time_before - self.__time_start).total_seconds() // 60)
        time_after = int((time_after - self.__time_start).total_seconds() // 60)
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(start >= time_before)
                
        for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(end <= time_after)
    
    def __apply_between_orders_constraint(self, client_id, activity_id: int, order_before: int, order_after: int, generate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two orders; start time of activity >= end time of another activity at order_before && end time of activity <= start time of another activity at order_after.

        Args:
            activity_id (int): the id of the activity
            order_before (int): the order of the other activity before
            order_after (int): the order of the other activity after
            generate (bool): whether to generate or avoid generating the constraint
        """
        
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(start >= self.__activity_index_end_time_int_vars[(client_id, order_before)])
                
        for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
            if generate:
                self.__model.Add(end <= self.__activity_index_start_time_int_vars[(client_id, order_after)])
    
    def __apply_within_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, time_after: timedelta, generate: bool):
        """[Activity Condition] Applies the condition that an activity must start within a certain time after another activity; start time of activity >= end time of another activity && start time of activity <= start time of another activity + time_after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_after (int): the time limit after the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        time_after = int(time_after.total_seconds() // 60)
        for start in self.__activity_start_time_int_vars[(client_id, activity_id)]:
            for end in self.__activity_end_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(start >= end)
            for other_start in self.__activity_start_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(start <= other_start + time_after)
    
    def __apply_within_before_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, time_before: timedelta, generate: bool):
        """[Activity Condition] Applies the condition that an activity must end within a certain time before another activity; end time of activity <= start time of another activity && end time of activity >= start time of another activity - time_before.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_before (int): the time limit before the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        time_before = int(time_before.total_seconds() // 60)
        for end in self.__activity_end_time_int_vars[(client_id, activity_id)]:
            for start in self.__activity_start_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(end <= start)
            for other_end in self.__activity_start_time_int_vars[(client_id, other_activity_id)]:
                if generate:
                    self.__model.Add(end >= other_end - time_before)
    
    def __apply_order_constraint(self, client_id, activity_id: int, order: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be at a certain order; start time of activity >= end time of other activities at < order && end time of activity <= start time of other activities at > order.

        Args:
            activity_id (int): the id of the activity
            client_id (int): the id of the client
            order (int): the order of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        matching_literals = [v for k, v in self.__activity_index_room_bool_vars.items() if k[0] == client_id and k[1] != activity_id and k[2] == order]
        for literal in matching_literals:
            if generate:
                self.__model.Add(literal == 0)
    
    def __apply_room_constraints(self):
        for room_id, conditions in self.__conditions_per_room.items():
            condition: Condition
            for condition in conditions:
                if condition.scope != ConditionScope.ROOM.value:
                    raise ValueError('Invalid condition scope for room constraint')
                
                if condition.option == RoomConditionOption.MAXIMUM.value:
                    if condition.option_type == RoomConditionOptionType.CLIENT.value:
                        self.__apply_maximum_capacity_constraint(**condition.args)
                    else:
                        raise ValueError('Invalid condition option type for maximum room constraint')
                elif condition.option == RoomConditionOption.UNIQUE.value:
                    if condition.option_type == RoomConditionOptionType.ACTIVITY.value:
                        self.__apply_unique_room_for_activity_constraint(**condition.args)
                    else:
                        raise ValueError('Invalid condition option type for unique room constraint')
                elif condition.option == RoomConditionOption.SAME.value:
                    if condition.option_type == RoomConditionOptionType.ACTIVITY.value:
                        self.__apply_same_room_for_activities_constraint(**condition.args)
                    else:
                        raise ValueError('Invalid condition option type for same room constraint')
                else:
                    raise ValueError('Invalid condition option')                    
    
    # Room Conditions
    def __apply_maximum_capacity_constraint(self, room_id: int, activity_id, capacity: int, generate: bool):
        """[Room Condition] Applies the condition that a room must have a maximum capacity; sum of clients in room <= capacity.

        Args:
            room_id (int): the id of the room
            capacity (int): the maximum capacity of the room
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            assert len(set([len(assessment.activities) for assessment in self.__assessments])) == 1, 'Inequal number of activities per assessment'
            for _, schedule in enumerate(self.__schedules):
                for activity_index, _ in enumerate(schedule):
                    self.__model.Add(sum(self.__activity_room_bool_vars[(room_id, activity_index, activity_id)]) <= capacity)
                break
    
    def __apply_unique_room_for_activity_constraint(self, room_id: int, activity_id: int, generate: bool):
        """[Room Condition] Applies the condition that an activity must be in a unique room; sum of activities in room <= 1.

        Args:
            activity_id (int): the id of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            assert len(set([len(assessment.activities) for assessment in self.__assessments])) == 1, 'Inequal number of activities per assessment'
            for _, schedule in enumerate(self.__schedules):
                for activity_index, _ in enumerate(schedule):
                    self.__model.AddAtMostOne(self.__activity_room_bool_vars[(room_id, activity_index, activity_id)])
                break
    
    def __apply_same_room_for_activities_constraint(self, room_id: int, activity_id: int, other_activity_id: int, generate: bool):
        """[Room Condition] Applies the condition that the two activities of client must be in the same room; room id of activity == room id of other activity.

        Args:
            client_id (int): the id of the client
            room_id (int): the id of the room
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            assert len(set([len(assessment.activities) for assessment in self.__assessments])) == 1, 'Inequal number of activities per assessment'
            for client_id, _ in enumerate(self.__schedules):
                literals = self.__client_activity_rooms[(client_id, activity_id, room_id)]
                other_literals = self.__client_activity_rooms[(client_id, other_activity_id, room_id)]
                
                self.__model.Add(sum([*literals, *other_literals]) != 1)
                self.__model.Add(sum([*literals, *other_literals]) <= 2 )
        
    @property
    def assessments(self) -> List[Assessment]:
        """Getter attribute for the assessments
        """
        return self.__assessments
    
    @assessments.setter
    def assessments(self, _assessments: List[Assessment]) -> None:
        """Setter attribute for the assessments
        """
        # TODO: Modify sort to be based on priority
        self.__assessments = sorted(_assessments, key=lambda a: a.name)
    
    def generate(self):
        assert self.__assessments is not None, 'Invalid assessments'
        
        self.__initialize_variables()
        self.__define_variables()
        self.__apply_general_constraints()
        self.__apply_activity_constraints()
        self.__apply_room_constraints()
        self.__define_objective()
        
        self.__solver = cp_model.CpSolver()
        self.__status = self.__solver.Solve(self.__model)
        
        if self.__status != cp_model.OPTIMAL:
            return self.__solver.StatusName(self.__status)
        
        for client_id, schedule in enumerate(self.__schedules):
            for literal, other_literal in zip(self.__client_activity_rooms[(client_id, 'Check-in, Consent & Change', 'St James')], self.__client_activity_rooms[(client_id, 'Lunch', 'St James')]):
                print(self.__solver.Value(literal), self.__solver.Value(other_literal))
            print(f'Client {client_id}')
            a = []
            for activity_index, activities in enumerate(schedule):
                s_a = None
                e_a = None
                for activity in activities:
                    if self.__solver.Value(self.__activity_index_room_bool_vars[(client_id, activity.id, activity_index, activity.room_id)]):
                        s_a = self.__solver.Value(self.__activity_index_start_time_int_vars[(client_id, activity_index)])
                        e_a = self.__solver.Value(self.__activity_index_end_time_int_vars[(client_id, activity_index)])
                        a.append((
                            activity.id,
                            activity.room_id,
                            s_a,
                            e_a,
                        ))
                        break
                
                if activity_index + 1 == len(schedule):
                    continue
                
                s_gt = self.__solver.Value(self.__transfer_start_time_int_vars[(client_id, activity_index, activity_index + 1)])
                e_gt = self.__solver.Value(self.__transfer_end_time_int_vars[(client_id, activity_index, activity_index + 1)])
                s_oa = self.__solver.Value(self.__activity_index_start_time_int_vars[(client_id, activity_index + 1)])
                if self.__solver.Value(self.__room_floor_bool_vars[(client_id, activity_index, activity_index + 1)]):
                    a.append((
                        'Transfer',
                        s_gt,
                        e_gt,
                    ))
                elif e_a != s_oa:
                    a.append((
                        'Gap',
                        e_a,
                        s_oa,
                    ))
                
            print(a)
        
        return self.__solver.StatusName(self.__status)
    
if __name__ == '__main__':
    TIME_START = timedelta(hours=7, minutes=15)
    TIME_END = timedelta(hours=18, minutes=0)
    TIME_MAX_INTERVAL = timedelta(hours=0, minutes=5)
    TIME_MAX_GAP = timedelta(hours=0, minutes=5)
    TIME_TRANSFER = timedelta(hours=0, minutes=5)
    
    NUM_FLOORS = 2

    NUM_ULT_CLIENTS = 0
    NUM_OPT_CLIENTS = 8

    NUM_CLIENT_ROOMS = 8
    NUM_BLOODS_ROOM = 1
    NUM_CONSULT_ROOMS = 3
    NUM_STRESS_ROOMS = 2
    NUM_MRI_15_ROOMS = 1
    NUM_MRI_3_ROOMS = 1
    NUM_ULTRASOUND_ROOMS = 2
    NUM_EYES_ROOMS = 1
    NUM_RAD_ROOMS = 1
    
    SIMULTANEOUS_TRANFERS = False
    
    SUM_1 = sum((NUM_CLIENT_ROOMS, NUM_ULTRASOUND_ROOMS))
    SUM_2 = sum((SUM_1, NUM_MRI_15_ROOMS))
    SUM_3 = sum((SUM_2, NUM_MRI_3_ROOMS))
    SUM_4 = sum((SUM_3, NUM_STRESS_ROOMS))
    SUM_5 = sum((SUM_4, NUM_CONSULT_ROOMS))
    SUM_6 = sum((SUM_5, NUM_EYES_ROOMS))
    SUM_7 = sum((SUM_6, NUM_BLOODS_ROOM))
    SUM_8 = sum((SUM_7, NUM_RAD_ROOMS))
    
    BASE_ROOM_ID = 300
    CLIENT_ROOMS = [
        Room(
            id=i,
            name=f'Client Room {i}',
            type=RoomType.CLIENT,
            floor=1,
            conditions=[
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    args=dict(activity_id=201, generate=True)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    args=dict(activity_id=208, generate=True)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    args=dict(activity_id=211, generate=True)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.SAME,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    args=dict(activity_ids=[201, 208, 211], generate=True)
                )
            ]
        ) for i in range(BASE_ROOM_ID + 1, BASE_ROOM_ID + NUM_CLIENT_ROOMS + 1)
    ]
    PHLEBOTOMY_ROOMS = [
        Room(
            id=i,
            name=f'Phelobotomy Room {i}',
            type=RoomType.OTHER,
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_6 + 1, BASE_ROOM_ID + SUM_7 + 1)
    ]
    CONSULTATION_ROOMS = [
        Room(
            id=i,
            name=f'Consultation Room {i}',
            type=RoomType.OTHER,
            floor=2,
            conditions=[
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.MAXIMUM,
                    option_type=RoomConditionOptionType.CLIENT,
                    args=dict(max_clients=3, generate=True)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.SAME,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    args=dict(activity_ids=[203, 210], generate=True)
                )
            ]
        ) for i in range(BASE_ROOM_ID + SUM_4 + 1, BASE_ROOM_ID + SUM_5 + 1)
    ]
    CARDIAC_ROOMS = [
        Room(
            id=i,
            name=f'Cardiac Room {i}',
            type=RoomType.OTHER,
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_3 + 1, BASE_ROOM_ID + SUM_4 + 1)
    ]
    MRI_ROOMS = [
        Room(
            id=i,
            name=f'MRI Room {n}',
            type=RoomType.OTHER,
            floor=2,
            conditions=[]
        ) for i, n in zip(range(BASE_ROOM_ID + SUM_1 + 1, BASE_ROOM_ID + SUM_2 + 1), [*(['1.5T'] * NUM_MRI_15_ROOMS), *(['3T'] * NUM_MRI_3_ROOMS)])
    ]
    ULTRASOUND_ROOMS = [
        Room(
            id=i,
            name=f'Ultrasound Room {i}',
            type=RoomType.OTHER,
            floor=2,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + NUM_CLIENT_ROOMS + 1, BASE_ROOM_ID + SUM_1 + 1)
    ]
    EYES_EARS_ROOMS = [
        Room(
            id=i,
            name=f'Eyes and Ears Room {i}',
            type=RoomType.OTHER,
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_5 + 1, BASE_ROOM_ID + SUM_6 + 1)
    ]
    RADIOLOGY_ROOMS = [
        Room(
            id=i,
            name=f'Radiology Room {i}',
            type=RoomType.OTHER,
            floor=2,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_7 + 1, BASE_ROOM_ID + SUM_8 + 1)
    ]
    
    solver = Solver(TIME_START, TIME_END, TIME_MAX_INTERVAL, TIME_MAX_GAP, TIME_TRANSFER, NUM_FLOORS, SIMULTANEOUS_TRANFERS)
    solver.assessments = [
        Assessment(
            id=101,
            name='Optimal',
            activities=[
                Activity(
                    id=201,
                    name='Check-in',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.IN_FIXED_ORDER_AS,
                            option_type=ActivityConditionOptionType.ORDER,
                            args=dict(activity_id=201, order=0, generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=10
                        ) for room in CLIENT_ROOMS
                    ]
                ),
                Activity(
                    id=202,
                    name='Bloods',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.IN_FIXED_ORDER_AS,
                            option_type=ActivityConditionOptionType.ORDER,
                            args=dict(activity_id=202, order=1, generate=True)
                        ),
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.WITHIN_AFTER,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            args=dict(activity_id=202, other_activity_id=201, time_after=timedelta(minutes=30), generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=10
                        ) for room in PHLEBOTOMY_ROOMS
                    ]
                ),
                Activity(
                    id=203,
                    name='First Consultation',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.BEFORE,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            args=dict(activity_id=203, other_activity_id=205, generate=True)
                        ),
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.WITHIN_AFTER,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            args=dict(activity_id=203, other_activity_id=201, time_after=timedelta(hours=2), generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=60
                        ) for room in CONSULTATION_ROOMS
                    ]
                ),
                Activity(
                    id=204,
                    name='Stress Echo',
                    conditions=[],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=50
                        ) for room in CARDIAC_ROOMS
                    ]
                ),
                Activity(
                    id=205,
                    name='MRI',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.BEFORE,
                            option_type=ActivityConditionOptionType.TIME,
                            args=dict(activity_id=205, time_before=timedelta(hours=16), generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=80
                        ) if '1.5T' in room.name else 
                        ActivityRoom(
                            room=room,
                            duration=20
                        ) for room in MRI_ROOMS
                    ]
                ),
                Activity(
                    id=206,
                    name='Ultrasound',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.BEFORE,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            args=dict(activity_id=206, other_activity_id=208, generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=60
                        ) for room in ULTRASOUND_ROOMS
                    ]
                ),
                Activity(
                    id=207,
                    name='Eyes & Ears',
                    conditions=[],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=10
                        ) for room in EYES_EARS_ROOMS
                    ]
                ),
                Activity(
                    id=208,
                    name='Lunch',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.BETWEEN,
                            option_type=ActivityConditionOptionType.TIME,
                            args=dict(activity_id=208, time_before=timedelta(hours=11), time_after=timedelta(hours=16), generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=10
                        ) for room in CLIENT_ROOMS
                    ]
                ),
                Activity(
                    id=209,
                    name='Radiologist Consultation',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.AFTER,
                            option_type=ActivityConditionOptionType.TIME,
                            args=dict(activity_id=209, time_after=timedelta(hours=13), generate=True)
                        ),
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.AFTER,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            args=dict(activity_id=209, other_activity_id=205, generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=25
                        ) for room in RADIOLOGY_ROOMS
                    ]
                ),
                Activity(
                    id=210,
                    name='Final Consultation',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.IN_FIXED_ORDER_AS,
                            option_type=ActivityConditionOptionType.ORDER,
                            args=dict(activity_id=210, order=9, generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=30
                        ) for room in CONSULTATION_ROOMS
                    ]
                ),
                Activity(
                    id=211,
                    name='Checkout',
                    conditions=[
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.IN_FIXED_ORDER_AS,
                            option_type=ActivityConditionOptionType.ORDER,
                            args=dict(activity_id=211, order=10, generate=True)
                        )
                    ],
                    rooms=[
                        ActivityRoom(
                            room=room,
                            duration=10
                        ) for room in CLIENT_ROOMS
                    ]
                ),
            ],
            quantity=NUM_OPT_CLIENTS
        )
    ]
    
    print(solver.generate())