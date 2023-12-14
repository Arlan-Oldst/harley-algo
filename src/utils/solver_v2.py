from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar
from typing import List, Dict, Tuple, Any
from src.models import solver_model as sm, model as m
from datetime import timedelta, datetime
import collections
import os

class Solver:
    """A class for solving the scheduling problem of the assessments.
    
    Assumptions:
    - The first and last activities are known
    - All assessments have the same activities
    - All assessments have the same room conditions
    """    
    def __init__(self) -> None:
        """Initializer for the solver

        Args:
            time_start (timedelta): the start time of the schedule
            time_end (timedelta): the end time of the schedule
            time_max_gap (timedelta): the maximum gap between activities
            time_transfer (timedelta): the time needed for transferring between activities
            num_floors (int): the names of the assessments
        """
        self.__time_start = None
        self.__time_end = None
        self.__time_max_interval = None
        self.__time_max_gap = None
        self.__time_transfer = None
        
        self.__num_floors = 0
        
        self.__simultaneous_transfers = None
        
        self.__horizon = None
        
        self.__activity_type = collections.namedtuple('task_type', 'duration id room_id room_floor')
        
        self.model = cp_model.CpModel()
        self.__scenario_action = None
        self.__resources = None
        self.__activities = None
        self.__assessments = None
        self.__general_conditions = None
        self.__room_conditions = None
        self.__schedules = []
        
        self.gaps = []
        self.floors = dict()
        self.rooms = dict()
        self.orders = dict()
        self.intervals = dict()
        self.starts = dict()
        self.ends = dict()
        
        self.ends_per_client = []
        
        self.starts_per_activity = collections.defaultdict(list)
        self.ends_per_activity = collections.defaultdict(list)
        self.intervals_per_room = collections.defaultdict(list)
        self.intervals_per_client =  collections.defaultdict(list)
        self.intervals_per_activity = collections.defaultdict(list)
        self.rooms_per_activity = collections.defaultdict(list)

        self.transfer_starts = dict()
        self.transfer_ends = dict()
        self.transfer_intervals = dict()
        self.transfer_precedences = dict()
        self.transfer_floors = dict()
    
    def __define_objective(self, mode: sm.SolverMode = sm.SolverMode.GAPS.value):
        """Helper function for defining the objective of the solver
        """
        assert len(self.ends_per_client) > 0, 'Invalid number of last activity end times'
        
        if mode == sm.SolverMode.MAKESPAN.value:
            makespan = self.model.NewIntVar(0, self.__horizon, 'makespan')
            self.model.AddMaxEquality(makespan, self.ends_per_client)
            self.model.Minimize(makespan)
        elif mode == sm.SolverMode.GAPS.value:
            self.model.Minimize(sum(self.gaps))
    
    def __initialize_variables(self):
        """Helper function for initializing the variables of the solver. It must be ran prior to the definition of the variables.
        """
        for index in range(0, len(self.assessments)):
            num_male_clients = getattr(self.scenario_action.data, f'client_{self.assessments[index].assessment_name.lower()}').single_male
            num_female_clients = getattr(self.scenario_action.data, f'client_{self.assessments[index].assessment_name.lower()}').single_female
            
            num_clients = num_male_clients + num_female_clients

            if not num_clients:
                self.assessments[index].enabled = False
                continue
            
            activities = self.assessments[index].data['activities']
            # TODO: Get duration according to gender if is_gender_time_allocated. Uses default for now
            # TODO: Activity ID for now is the activity name
            schedule = []
            _activities: List[m.Activity]
            for _activities in activities:
                activity_rooms = []
                
                activity: m.Activity
                for activity in _activities:
                    
                    room_type = activity.room_type if activity.resource_type == m.ResourceTypes.OTHER else m.ResourceTypes.CLIENT.value
                    rooms = self.__rooms_map[room_type]
                    room: m.Resource
                    for room in rooms:
                        duration = activity.time_allocations.default_time
                        
                        if activity.is_gender_time_allocated:
                            # TODO: support gender time allocated
                            pass
                        
                        activity_rooms.append(self.__activity_type(duration, activity.activity_id, room.resource_id, room.location))
                        
                        self.__num_floors = max(self.__num_floors, room.location)
                        
                schedule.append(activity_rooms)
                    
            self.__schedules.extend([schedule] * num_clients)
    
    def __define_variables(self):
        """Helper function for defining the variables of the solver
        """
        assert len(self.__schedules) > 0, 'Invalid schedules'
        start_time = datetime.now()
        
        previous_start = None
        for client_id, schedule in enumerate(self.__schedules):
            previous_end = None
            
            for i, activities in enumerate(schedule):
                activity = activities[0]
                                
                min_duration = activities[0].duration
                max_duration = activities[0].duration
                
                for activity_room in activities[1:]:
                    min_duration = min(min_duration, activity_room.duration)
                    max_duration = max(max_duration, activity_room.duration)
                
                suffix = f'_c{client_id}_a{activity.id}'
                start = self.model.NewIntVar(0, self.__horizon, f'start{suffix}')
                duration = self.model.NewIntVar(min_duration, max_duration, f'duration{suffix}')
                end = self.model.NewIntVar(0, self.__horizon, f'end{suffix}')
                interval = self.model.NewIntervalVar(start, duration, end, f'interval{suffix}')
                floor = self.model.NewIntVar(0, self.__num_floors, f'floor{suffix}')
                order = self.model.NewIntVar(0, len(schedule) - 1, f'order{suffix}')
                
                self.starts[(client_id, activity.id)] = start
                self.ends[(client_id, activity.id)] = end
                self.intervals[(client_id, activity.id)] = interval
                self.floors[(client_id, activity.id)] = floor
                self.orders[(client_id, activity.id)] = order
                
                self.model.AddModuloEquality(0, start, self.__time_max_interval)
                self.model.AddModuloEquality(0, end, self.__time_max_interval)
                               
                previous_end = end
                if i == 0:
                    if previous_start == None:
                        self.model.Add(start == 0)
                    else:
                        self.model.Add(start > previous_start)
                    previous_start = start
                        
                self.starts_per_activity[activity.id].append(start)
                self.ends_per_activity[activity.id].append(end)
                  
                if len(activities) > 1:
                    current_activity_rooms = []
                    for activity_room in activities:
                        other_suffix = f'_c{client_id}_a{activity.id}_r{activity_room.room_id}'
                        current_start = self.model.NewIntVar(0, self.__horizon, f'start{other_suffix}')
                        current_duration = activity_room.duration
                        current_end = self.model.NewIntVar(0, self.__horizon, f'end{other_suffix}')
                        current_room = self.model.NewBoolVar(f'room{other_suffix}')
                        current_interval = self.model.NewOptionalIntervalVar(current_start, current_duration, current_end, current_room, f'interval{other_suffix}')
                        current_floor = self.model.NewIntVar(0, self.__num_floors, f'floor{other_suffix}')
                        
                        current_activity_rooms.append(current_room)
                        self.intervals_per_room[activity_room.room_id].append(current_interval)
                        self.intervals_per_client[client_id].append(current_interval)
                        self.intervals_per_activity[activity.id].append(current_interval)
                        self.rooms_per_activity[(activity.id, activity_room.room_id)].append(current_room)
                        
                        self.rooms[(client_id, activity.id, activity_room.room_id)] = current_room
                        
                        self.model.Add(current_start == start).OnlyEnforceIf(current_room)
                        self.model.Add(current_end == end).OnlyEnforceIf(current_room)
                        self.model.Add(current_duration == duration).OnlyEnforceIf(current_room)                        
                        self.model.Add(current_floor == activity_room.room_floor).OnlyEnforceIf(current_room)
                        self.model.Add(current_floor == floor).OnlyEnforceIf(current_room)
                        
                    self.model.AddExactlyOne(current_activity_rooms)
                else:
                    self.intervals_per_room[activity.room_id].append(interval)
                    self.intervals_per_client[client_id].append(interval)
                    self.intervals_per_activity[activity.id].append(interval)
                    
                    self.rooms[(client_id, activity.id, activity.room_id)] = self.model.NewConstant(1)
                    
                    self.model.Add(floor == activity.room_floor)
                
            self.ends_per_client.append(previous_end)
        
        end_time = datetime.now()
        print(f'Total Time for defining variables: {(end_time - start_time).total_seconds() / 60.0} minutes')
    
    def __apply_general_constraints(self):
        """Helper function for applying all general constraints of the solver namely:
        
        - Generate Optimal before Ultimate
        - Transfers can either be simultaneous or not
        - No overlap between activities
        - All activities must be performed
        - All times must be divisible by 5
        - Room conditions
        """
        start_time = datetime.now()
        
        for client_id, schedule in enumerate(self.__schedules):
            self.__apply_no_overlap_client_constraint(client_id)
            self.__apply_same_room_for_activities_constraint(client_id, 'Check-in, Consent & Change', 'Lunch')
            self.__apply_same_room_for_activities_constraint(client_id, 'Check-in, Consent & Change', 'Checkout')
                
        for room_id in self.intervals_per_room.keys():
            self.__apply_no_overlap_room_constraint(room_id)
            
            key = ('Check-in, Consent & Change', room_id)
            if key in self.rooms_per_activity:
                self.__apply_unique_room_for_activity_constraint(room_id, 'Check-in, Consent & Change')
                
            key = ('First Consultation', room_id)
            if key in self.rooms_per_activity:
                self.__apply_maximum_capacity_constraint(room_id, 'First Consultation', 3)
                
            key = ('Final Consultation', room_id)
            if key in self.rooms_per_activity:
                self.__apply_maximum_capacity_constraint(room_id, 'First Consultation', 3)
        
        self.__apply_transfer_constraint()
        self.__apply_maximum_time_constraint()
        self.__apply_simultaneous_transfers_constraint(self.__simultaneous_transfers)
        self.__apply_no_overlap_activity_constraint('Check-in, Consent & Change')
        self.__apply_gap_between_activity_constraint('MRI')
        
        end_time = datetime.now()
        print(f'Total Time for applying general constraints: {(end_time - start_time).total_seconds() / 60.0} minutes')
    
    def __apply_no_overlap_activity_constraint(self, activity_id: int):
        """Helper function for applying the no overlap constraint at the activity level of the solver.
        """
        self.model.AddNoOverlap(self.intervals_per_activity[activity_id])
    
    def __apply_no_overlap_client_constraint(self, client_id: int):
        """Helper function for applying the no overlap constraint at the client level of the solver.
        """
        self.model.AddNoOverlap(self.intervals_per_client[client_id])
    
    def __apply_no_overlap_room_constraint(self, room_id: int):
        """Helper function for applying the no overlap constraint at the room level of the solver.
        """
        self.model.AddNoOverlap(self.intervals_per_room[room_id])
    
    def __apply_gap_between_activity_constraint(self, activity_id: int):
        """Helper function for applying the gap between activities at specific room of the solver. Forces time max interval gaps between activities at specific room.
        """
        for start in self.starts_per_activity[activity_id]:
            for end in self.ends_per_activity[activity_id]:
                self.model.Add(start != end)
                
            for other_start in self.starts_per_activity[activity_id]:
                if start == other_start:
                    continue
                
                self.model.Add(start != other_start)
                
        for end in self.ends_per_activity[activity_id]:
            for other_end in self.ends_per_activity[activity_id]:
                if end == other_end:
                    continue
                
                self.model.Add(end != other_end)
    
    def __apply_simultaneous_transfers_constraint(self, generate: bool = True):
        """Helper function for applying allowing simultaneous transfers constraint of the solver.
        """
        if not generate:
            self.model.AddNoOverlap(self.transfer_intervals.values())
    
    def __apply_transfer_constraint(self):
        """Helper function for applying the transfer constraint of the solver.
        """
        for client_id, schedule in enumerate(self.__schedules):
            arcs = []
            for activity_index, activities in enumerate(schedule):
                activity_id = activities[0].id
                first_activity = self.model.NewBoolVar(f'{activity_index} is first activity')
                last_activity = self.model.NewBoolVar(f'{activity_index} is last activity')
                
                arcs.append((0, activity_index + 1, first_activity))
                arcs.append((activity_index + 1, 0, last_activity))
                
                for other_activity_index, other_activities in enumerate(schedule):
                    if activity_index == other_activity_index:
                        continue
                    other_activity_id = other_activities[0].id
                    consecutive_activities = self.model.NewBoolVar(f'{other_activity_id} is after {activity_id}')
                    self.transfer_precedences[(client_id, activity_index, other_activity_index)] = consecutive_activities
                    
                    arcs.append((activity_index + 1, other_activity_index + 1, consecutive_activities))
                    
                    self.model.Add(self.orders[(client_id, other_activity_id)] > self.orders[(client_id, activity_id)]).OnlyEnforceIf(consecutive_activities)
                    
                    suffix = f'_trf_c_{client_id}_a_{activity_id}_a_{other_activity_id}'
                    transfer_floor = self.model.NewBoolVar(f'floor{suffix}')
                    self.model.Add(self.floors[(client_id, activity_id)] != self.floors[(client_id, other_activity_id)]).OnlyEnforceIf(transfer_floor)
                    self.model.Add(self.floors[(client_id, activity_id)] == self.floors[(client_id, other_activity_id)]).OnlyEnforceIf(transfer_floor.Not())
                    
                    transfer_start = self.model.NewIntVar(0, self.__horizon, f'start{suffix}')
                    transfer_end = self.model.NewIntVar(0, self.__horizon, f'end{suffix}')
                    transfer_duration = self.__time_transfer
                    transfer_interval = self.model.NewOptionalIntervalVar(transfer_start, transfer_duration, transfer_end, consecutive_activities, f'interval{suffix}')
                    
                    self.model.Add(transfer_start == self.ends[(client_id, activity_id)]).OnlyEnforceIf(transfer_floor, consecutive_activities)
                    self.model.Add(transfer_end == self.starts[(client_id, other_activity_id)]).OnlyEnforceIf(transfer_floor, consecutive_activities)
                    
                    self.model.Add(self.starts[(client_id, other_activity_id)] == self.ends[(client_id, activity_id)]).OnlyEnforceIf(transfer_floor.Not(), consecutive_activities)
                    # self.model.Add(self.starts[(client_id, other_activity_id)] - self.ends[(client_id, activity_id)] <= self.__time_max_gap).OnlyEnforceIf(transfer_floor.Not(), consecutive_activities)
                    
                    self.model.AddModuloEquality(0, transfer_start, self.__time_max_interval)
                    self.model.AddModuloEquality(0, transfer_end, self.__time_max_interval)
                    
                    # For getting the number of gaps
                    consecutive_orders = self.model.NewBoolVar(f'{other_activity_id} order is after {activity_id} order')
                    self.model.Add(self.starts[(client_id, other_activity_id)] - self.ends[(client_id, activity_id)] <= self.__time_max_gap).OnlyEnforceIf(consecutive_orders)
                    self.model.Add(self.starts[(client_id, other_activity_id)] - self.ends[(client_id, activity_id)] > self.__time_max_gap).OnlyEnforceIf(consecutive_orders.Not())
                    
                    zero_time_difference = self.model.NewBoolVar(f'difference of {other_activity_id} and {activity_id} is equal to zero')
                    self.model.Add(self.starts[(client_id, other_activity_id)] - self.ends[(client_id, activity_id)] != 0).OnlyEnforceIf(zero_time_difference)
                    self.model.Add(self.starts[(client_id, other_activity_id)] - self.ends[(client_id, activity_id)] == 0).OnlyEnforceIf(zero_time_difference.Not())
                    
                    existing_gap = self.model.NewBoolVar(f'gap between {other_activity_id} and {activity_id} exists')
                    self.model.Add(existing_gap == 1).OnlyEnforceIf(transfer_floor.Not(), consecutive_activities, consecutive_orders, zero_time_difference)
                    self.model.Add(existing_gap == 0).OnlyEnforceIf(transfer_floor.Not(), consecutive_activities, consecutive_orders, zero_time_difference.Not())
                    
                    self.gaps.append(existing_gap)
                    
                    self.transfer_starts[(client_id, activity_index, other_activity_index)] = transfer_start
                    self.transfer_ends[(client_id, activity_index, other_activity_index)] = transfer_end
                    self.transfer_intervals[(client_id, activity_index, other_activity_index)] = transfer_interval
                    
                    self.transfer_floors[(client_id, activity_index, other_activity_index)] = transfer_floor
                    
                    self.intervals_per_client[client_id].append(transfer_interval)
                    
            self.model.AddCircuit(arcs)
    
    def __apply_maximum_time_constraint(self, generate: bool = True):
        """Helper function for applying the maximum time constraint of the solver.
        """
        if generate:
            for end in self.ends_per_client:
                self.model.Add(end <= self.__horizon)
    
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
        start_time = datetime.now()
        
        start_activity_id = self.__activities_names_map['Check-in, Consent & Change'][0].activity_id
        for assessment in self.assessments:
            if not assessment.enabled:
                continue
            
            condition: m.Condition
            for condition in assessment.data['activity_conditions']:
                if condition.deleted:
                    continue
                
                if not condition.mandatory:
                    continue
                
                condition_type = condition.type
                condition_activity_id = condition.activity_id
                condition_criteria_value = condition.criteria.value
                condition_criteria_between_values_start = condition.criteria.between_values.start
                condition_criteria_between_values_end = condition.criteria.between_values.end
                condition_criteria_type = condition.criteria.criteria_type
                
                if condition_criteria_type == m.CriteriaTypes.TIME and condition_type != m.ConditionTypes.BETWEEN:
                    if condition_type == m.ConditionTypes.WITHIN:
                        condition_criteria_value = timedelta(minutes=int(condition_criteria_value))
                    else:
                        time_value = datetime.strptime(condition_criteria_value, "%H:%M")
                        condition_criteria_value = timedelta(hours=time_value.hour, minutes=time_value.minute, seconds=time_value.second)
                elif condition_criteria_type == m.CriteriaTypes.ORDER and condition_type != m.ConditionTypes.BETWEEN:
                    condition_criteria_value = int(condition_criteria_value)
                elif condition_criteria_type == m.CriteriaTypes.TIME and condition_type == m.ConditionTypes.BETWEEN:
                    before_time_value = datetime.strptime(condition_criteria_between_values_start, "%H:%M")
                    condition_criteria_between_values_start = timedelta(hours=before_time_value.hour, minutes=before_time_value.minute, seconds=before_time_value.second)
                    after_time_value = datetime.strptime(condition_criteria_between_values_end, "%H:%M")
                    condition_criteria_between_values_end = timedelta(hours=after_time_value.hour, minutes=after_time_value.minute, seconds=after_time_value.second)
                elif condition_criteria_type == m.CriteriaTypes.ORDER and condition_type == m.ConditionTypes.BETWEEN:
                    condition_criteria_between_values_start = int(condition_criteria_between_values_start)
                    condition_criteria_between_values_end = int(condition_criteria_between_values_end)
                elif condition_type == m.ConditionTypes.WITHIN:
                    time_value = datetime.strptime(condition_criteria_value, "%H:%M")
                    condition_criteria_value = timedelta(hours=time_value.hour, minutes=time_value.minute, seconds=time_value.second)
                
                for client_id, _ in enumerate(self.__schedules):
                    # if condition_type == m.ConditionTypes.BEFORE:
                    #     if condition_criteria_type == m.CriteriaTypes.ACTIVITY:
                    #         self.__apply_before_activity_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     elif condition_criteria_type == m.CriteriaTypes.TIME:
                    #         self.__apply_before_time_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     elif condition_criteria_type == m.CriteriaTypes.ORDER:
                    #         self.__apply_before_order_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     # else:
                    #     #     raise ValueError('Invalid condition option type for before activity constraint')
                    # elif condition_type == m.ConditionTypes.AFTER:
                    #     if condition_criteria_type == m.CriteriaTypes.ACTIVITY:
                    #         self.__apply_after_activity_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     elif condition_criteria_type == m.CriteriaTypes.TIME:
                    #         self.__apply_after_time_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     elif condition_criteria_type == m.CriteriaTypes.ORDER:
                    #         self.__apply_after_order_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     # else:
                    #     #     raise ValueError('Invalid condition option type for after activity constraint')
                    # elif condition_type == m.ConditionTypes.RIGHT_AFTER:
                    #     if condition_criteria_type == m.CriteriaTypes.ACTIVITY:
                    #         self.__apply_right_after_activity_constraint(client_id, condition_activity_id, condition_criteria_value)
                    #     # else:
                    #     #     raise ValueError('Invalid condition option type for right after activity constraint')
                    # elif condition_type == m.ConditionTypes.BETWEEN:
                    #     if condition_criteria_type == m.CriteriaTypes.ACTIVITY:
                    #         self.__apply_between_activities_constraint(client_id, condition_activity_id, condition_criteria_between_values_start, condition_criteria_between_values_end)
                    #     elif condition_criteria_type == m.CriteriaTypes.TIME:
                    #         self.__apply_between_times_constraint(client_id, condition_activity_id, condition_criteria_between_values_start, condition_criteria_between_values_end)
                    #     elif condition_criteria_type == m.CriteriaTypes.ORDER:
                    #         self.__apply_between_orders_constraint(client_id, condition_activity_id, condition_criteria_between_values_start, condition_criteria_between_values_end)
                    #     # else:
                    #     #     raise ValueError('Invalid condition option type for between constraint')
                    # elif condition_type == m.ConditionTypes.WITHIN:
                    #     other_activity_id = start_activity_id
                    #     self.__apply_within_after_activity_constraint(client_id, condition_activity_id, other_activity_id, condition_criteria_value)
                    if condition_type == m.ConditionTypes.IN_FIXED_ORDER_AS:
                        if condition_criteria_type == m.CriteriaTypes.ORDER:
                            self.__apply_order_constraint(client_id, condition_activity_id, condition_criteria_value)
                        # else:
                        #     raise ValueError('Invalid condition option type for in fixed order as constraint')
                    # else:
                    #     raise ValueError('Invalid condition option')
        
        end_time = datetime.now()
        print(f'Total Time for applying activity constraints: {(end_time - start_time).total_seconds() / 60.0} minutes')
        
    # Activity Conditions
    def __apply_before_activity_constraint(self, client_id: int, activity_id: int, other_activity_id: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be before another activity; end time of activity <= start time of another activity. 

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            before_activity_id (int): the id of the other acti vity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.ends[(client_id, activity_id)] <= self.starts[(client_id, other_activity_id)])
        
    def __apply_before_time_constraint(self, client_id: int, activity_id: int, time_before: timedelta, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be before a certain time; end time of activity <= time_before.

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            time_before (int): the maximum time limit for the end of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            time_before = int((time_before - self.__time_start).total_seconds() // 60)
            self.model.Add(self.ends[(client_id, activity_id)] <= time_before)           
    
    def __apply_before_order_constraint(self, client_id, activity_id: int, order: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be before a certain order; end time of activity <= start time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.orders[(client_id, activity_id)] < order)
    
    def __apply_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be after another activity; start time of activity >= end time of another activity.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.starts[(client_id, activity_id)] >= self.ends[(client_id, other_activity_id)])
    
    def __apply_after_time_constraint(self, client_id, activity_id: int, time_after: timedelta, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be after a certain time; start time of activity >= time_after.

        Args:
            activity_id (int): the id of the activity
            time_after (int): the minimum time limit for the start of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            time_after = int((time_after - self.__time_start).total_seconds() // 60)
            self.model.Add(self.starts[(client_id, activity_id)] >= time_after)
    
    def __apply_after_order_constraint(self, client_id, activity_id: int, order: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be after a certain order; start time of activity >= end time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.orders[(client_id, activity_id)] > order)
    
    def __apply_right_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be right after another activity; start time of activity >= end time of another activity && start time of activity - end time of another activity <= time_max_gap.

        Args:
            client_id (int): the id of the client
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_max_gap (int): the maximum time gap between the two activities
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.starts[(client_id, activity_id)] == self.ends[(client_id, other_activity_id)])
    
    def __apply_between_activities_constraint(self, client_id, activity_id: int, other_activity_id_before: int, other_activity_id_after: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be between two other activities; start time of activity >= end time of another activity before && end time of activity <= start time of another activity after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id_before (int): the id of the other activity before
            other_activity_id_after (int): the id of the other activity after
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.starts[(client_id, activity_id)] >= self.ends[(client_id, other_activity_id_before)])

            self.model.Add(self.ends[(client_id, activity_id)] <= self.starts[(client_id, other_activity_id_after)])
    
    def __apply_between_times_constraint(self, client_id, activity_id: int, time_before: timedelta, time_after: timedelta, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be between two times; start time of activity >= time_before && end time of activity <= time_after.

        Args:
            activity_id (int): the id of the activity
            time_before (int): the minimum time limit for the start of the activity
            time_after (int): the maximum time limit for the end of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            time_before = int((time_before - self.__time_start).total_seconds() // 60)
            time_after = int((time_after - self.__time_start).total_seconds() // 60)
            self.model.Add(self.starts[(client_id, activity_id)] >= time_before)
                
            self.model.Add(self.ends[(client_id, activity_id)] <= time_after)
    
    def __apply_between_orders_constraint(self, client_id, activity_id: int, order_before: int, order_after: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be between two orders; start time of activity >= end time of another activity at order_before && end time of activity <= start time of another activity at order_after.

        Args:
            activity_id (int): the id of the activity
            order_before (int): the order of the other activity before
            order_after (int): the order of the other activity after
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.orders[(client_id, activity_id)] > order_after)
            self.model.Add(self.orders[(client_id, activity_id)] < order_before)
    
    def __apply_within_after_activity_constraint(self, client_id, activity_id: int, other_activity_id: int, time_after: timedelta, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must start within a certain time after another activity; start time of activity >= end time of another activity && start time of activity <= start time of another activity + time_after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_after (int): the time limit after the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            time_after = int(time_after.total_seconds() // 60)
            self.model.Add(self.starts[(client_id, activity_id)] >= self.ends[(client_id, other_activity_id)])
            self.model.Add(self.starts[(client_id, activity_id)] <= self.starts[(client_id, other_activity_id)] + time_after)
    
    def __apply_order_constraint(self, client_id, activity_id: int, order: int, generate: bool = True):
        """[Activity Condition] Applies the condition that an activity must be at a certain order; start time of activity >= end time of other activities at < order && end time of activity <= start time of other activities at > order.

        Args:
            activity_id (int): the id of the activity
            client_id (int): the id of the client
            order (int): the order of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(self.orders[(client_id, activity_id)] == order)
    
    # def __apply_room_constraints(self):
    #     start_time = datetime.now()
        
    #     for room_id, conditions in self.__room_conditions:
    #         condition: sm.Condition
    #         for condition in conditions:
    #             if condition.scope != sm.ConditionScope.ROOM.value:
    #                 raise ValueError('Invalid condition scope for room constraint')
                
    #             if condition.option == sm.RoomConditionOption.MAXIMUM.value:
    #                 if condition.option_type == sm.RoomConditionOptionType.CLIENT.value:
    #                     self.__apply_maximum_capacity_constraint(**condition.args)
    #                 else:
    #                     raise ValueError('Invalid condition option type for maximum room constraint')
    #             elif condition.option == sm.RoomConditionOption.UNIQUE.value:
    #                 if condition.option_type == sm.RoomConditionOptionType.ACTIVITY.value:
    #                     self.__apply_unique_room_for_activity_constraint(**condition.args)
    #                 else:
    #                     raise ValueError('Invalid condition option type for unique room constraint')
    #             elif condition.option == sm.RoomConditionOption.SAME.value:
    #                 if condition.option_type == sm.RoomConditionOptionType.ACTIVITY.value:
    #                     self.__apply_same_room_for_activities_constraint(**condition.args)
    #                 else:
    #                     raise ValueError('Invalid condition option type for same room constraint')
    #             else:
    #                 raise ValueError('Invalid condition option')

    #     end_time = datetime.now()
    #     print(f'Total Time for applying room constraints: {(end_time - start_time).total_seconds() / 60.0} minutes')
    
    # # Room Conditions
    def __apply_maximum_capacity_constraint(self, room_id: int, activity_id, capacity: int, generate: bool = True):
        """[Room Condition] Applies the condition that a room must have a maximum capacity; sum of clients in room <= capacity.

        Args:
            room_id (int): the id of the room
            capacity (int): the maximum capacity of the room
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.Add(sum(self.rooms_per_activity[(activity_id, room_id)]) <= capacity)
    
    def __apply_unique_room_for_activity_constraint(self, room_id: int, activity_id: int, generate: bool = True):
        """[Room Condition] Applies the condition that an activity must be in a unique room; sum of activities in room <= 1.

        Args:
            activity_id (int): the id of the activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            self.model.AddAtMostOne(self.rooms_per_activity[(activity_id, room_id)])
    
    def __apply_same_room_for_activities_constraint(self, client_id: int, activity_id: int, other_activity_id: int, generate: bool = True):
        """[Room Condition] Applies the condition that the two activities of client must be in the same room; room id of activity == room id of other activity.

        Args:
            client_id (int): the id of the client
            room_id (int): the id of the room
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            generate (bool): whether to generate or avoid generating the constraint
        """
        if generate:
            activity_rooms = [(key[2], value) for key, value in self.rooms.items() if key[0] == client_id and key[1] == activity_id]
            other_activity_rooms = [(key[2], value) for key, value in self.rooms.items() if key[0] == client_id and key[1] == other_activity_id]
            
            assert len(activity_rooms) == len(other_activity_rooms), 'Invalid number of rooms for same room constraint'
            activity_rooms.sort(key=lambda a: a[0])
            other_activity_rooms.sort(key=lambda a: a[0])
            
            for (_, room), (_, other_room) in zip(activity_rooms, other_activity_rooms):
                self.model.Add(room == other_room)
        
    @property
    def scenario_action(self) -> m.ScenarioAction:
        """Getter attribute for the assessments
        """
        return self.__scenario_action
    
    @scenario_action.setter
    def scenario_action(self, _scenario_action: dict) -> None:
        """Setter attribute for the assessments
        """
        if not isinstance(_scenario_action, m.ScenarioAction):
            _scenario_action_data = _scenario_action.pop('data')
            self.__scenario_action = m.ScenarioAction(
                **_scenario_action,
                data=m.ScenarioActionData(
                    out_order_rooms=_scenario_action_data['out_of_order_rooms'],
                    client_elite=m.ClientElite(**_scenario_action_data['client_elite']),
                    client_ultimate=m.ClientUltimate(**_scenario_action_data['client_ultimate']),
                )
            )
        else:
            self.__scenario_action = _scenario_action
        
        first_client_arrival_time = datetime.strptime(self.__scenario_action.first_client_arrival_time,"%H:%M")
        self.__time_start = timedelta(hours=first_client_arrival_time.hour, minutes=first_client_arrival_time.minute, seconds=first_client_arrival_time.second)
        self.__time_end = timedelta(hours=18)
        self.__time_max_interval = int(timedelta(minutes=5).total_seconds() // 60)
        self.__time_max_gap = int(timedelta(minutes=self.__scenario_action.max_gap).total_seconds() // 60)
        self.__time_transfer = int(timedelta(minutes=5).total_seconds() // 60)
                
        self.__simultaneous_transfers = self.__scenario_action.allow_simultaneous_transfers
        
        self.__horizon = int((self.__time_end - self.__time_start).total_seconds() // 60)
    
    @property
    def resources(self) -> List[m.Resource]:
        """Getter attribute for the resources
        """
        return self.__resources
    
    @resources.setter
    def resources(self, _resources: List[dict]) -> None:
        """Setter attribute for the resources
        """
        assert len(_resources), 'Invalid resources'
        
        if not isinstance(_resources[0], m.Resource):
            self.__resources = [
                m.Resource(**resource)
                for resource in _resources
            ]
        else:
            self.__resources = _resources
            
        self.__rooms_map = collections.defaultdict(list)
        for resource in self.__resources:
            if resource.type == m.ResourceTypes.CLIENT:
                resource.data['room'] = m.ResourceTypes.CLIENT.value
            else:
                resource.data['room'] = resource.room_type.value
            self.__rooms_map[resource.data['room']].append(resource)
        
    @property
    def activities(self) -> List[m.Activity]:
        """Getter attribute for the activities
        """
        return self.__activities
    
    @activities.setter
    def activities(self, _activities: List[dict]) -> None:
        """Setter attribute for the activities
        """
        assert len(_activities), 'Invalid activities'
        
        if not isinstance(_activities[0], m.Activity):
            _time_allocations = [
                activity.pop('time_allocations')
                for activity in _activities
            ]
            self.__activities = [
                m.Activity(
                    **activity,
                    time_allocations=m.TimeAllocation(
                        **time_allocations
                    )
                )
                for activity, time_allocations in zip(_activities, _time_allocations)
            ]
            
            self.__activities_names_map = collections.defaultdict(list)
            for activity in self.__activities:
                for time_allocation in activity.time_allocations.__dict__:
                    self.__activities_names_map[(activity.activity_id, time_allocation)].append({
                        'id': activity.activity_id,
                        'room_type': activity.room_type,
                        'resource_type': activity.resource_type,
                        'duration': getattr(activity.time_allocations, time_allocation)
                    })
        else:
            self.__activities = _activities
    
    @property
    def activities_names_map(self) -> List[m.Activity]:
        """Getter attribute for the activities map
        """
        return self.__activities_names_map
    
    @activities_names_map.setter
    def activities_names_map(self, _activities_map: Dict[str, list]) -> None:
        """Setter attribute for the activities map
        """
        self.__activities_names_map = _activities_map
        
    @property
    def activities_ids_map(self) -> List[m.Activity]:
        """Getter attribute for the activities map
        """
        return self.__activities_ids_map
    
    @activities_ids_map.setter
    def activities_ids_map(self, _activities_map: Dict[str, list]) -> None:
        """Setter attribute for the activities map
        """
        self.__activities_ids_map = _activities_map
    
    @property
    def assessments(self) -> List[m.Assessment]:
        """Getter attribute for the assessments
        """
        return self.__assessments
    
    @assessments.setter
    def assessments(self, _assessments: List[dict]) -> None:
        """Setter attribute for the assessments
        """
        assert len(_assessments), 'Invalid assessments'
        
        if not isinstance(_assessments[0], m.Assessment):
            # TODO: Modify sort to be based on priority
            self.__assessments = [
                m.Assessment(
                    **assessment
                )
                for assessment in _assessments
            ]
        else:
            self.__assessments = _assessments
        
    @property
    def general_conditions(self) -> List[m.GeneralCondition]:
        """Getter attribute for the assessments
        """
        return self.__general_conditions
    
    @general_conditions.setter
    def general_conditions(self, _general_conditions: List[dict]) -> None:
        """Setter attribute for the general conditions
        """
        assert len(_general_conditions), 'Invalid general conditions'
        
        if not isinstance(_general_conditions[0], m.GeneralCondition):
            self.__general_conditions = [
                m.GeneralCondition(
                    **general_condition
                )
                for general_condition in _general_conditions
            ]
        else:
            self.__general_conditions = _general_conditions
    
    @property
    def room_conditions(self) -> List[sm.Condition]:
        """Getter attribute for the room conditions
        """
        return self.__activities
    
    @room_conditions.setter
    def room_conditions(self, _room_conditions: List[dict]) -> None:
        """Setter attribute for the room conditions
        """
        self.__assessments = [
            sm.Condition(
                **room_condition
            )
            for room_condition in _room_conditions
        ]
    
    def generate(self):
        assert self.__assessments is not None, 'Invalid assessments'
        
        self.__initialize_variables()
        self.__define_variables()
        # self.__apply_general_constraints()
        # self.__apply_activity_constraints()
        # self.__apply_room_constraints()
        self.__define_objective()
        
        self.__solver = cp_model.CpSolver()
        self.__solver.parameters.max_time_in_seconds = timedelta(minutes=int(os.getenv('SOLVER_MAX_TIME_MINUTES', 5))).total_seconds()
        
        start_time = datetime.now()
        self.__status = self.__solver.Solve(self.model)        
        end_time = datetime.now()
        
        print(self.__solver.StatusName(self.__status))
        print(f'Total Time for solver: {(end_time - start_time).total_seconds() / 60.0} minutes')
        
        
        if self.__status != cp_model.OPTIMAL and self.__status != cp_model.FEASIBLE:
            raise ValueError('Cannot generate schedule')
        
        self.__generated_schedules = []
        
        for client_id, _ in enumerate(self.__schedules):
            generated_schedule = []
            activities = [(key[1], self.__solver.Value(value)) for key, value in self.starts.items() if key[0] == client_id]
            activities.sort(key=lambda activity: activity[1])
            
            for activity_id, start in activities:
                room = next((key[2] for key, value in self.rooms.items() if key[0] == client_id and key[1] == activity_id and self.__solver.Value(value)))
                floor = self.floors[(client_id, activity_id)]
                end = self.ends[(client_id, activity_id)]
                generated_schedule.append([
                    activity_id,
                    room,
                    self.__solver.Value(floor),
                    start,
                    self.__solver.Value(end),
                ])
                
            for key, value in self.transfer_starts.items():
                if self.__solver.Value(self.transfer_precedences[key]) and self.__solver.Value(self.transfer_floors[key]) and key[0] == client_id:
                    generated_schedule.append([
                        'Transfer',
                        'None',
                        'None',
                        self.__solver.Value(value),
                        self.__solver.Value(self.transfer_ends[key]),
                    ])
            self.__generated_schedules.append(sorted(generated_schedule, key=lambda activity: activity[3]))
        
        return self.__generated_schedules