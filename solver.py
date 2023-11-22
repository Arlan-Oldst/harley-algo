from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar
from typing import List, Dict, Tuple
from models import Client, Condition, Activity, ActivityRoom, Assessment, ConditionScope, ActivityConditionOption, ActivityConditionOptionType, RoomConditionOption, RoomConditionOptionType, Room
from datetime import timedelta
import collections

"""
Rules:
- General Conditions are hard-coded.
- A client must have an id, type, and list of activities
- An activity must have an id, duration, list of rooms, and list of conditions
- A room must have an id, floor, and list of conditions

- A condition is assumed as a singleton
"""

class Solver:
    def __init__(self, time_start: timedelta, time_end: timedelta, time_max_interval: timedelta, time_max_gap: timedelta, time_transfer: timedelta, num_floors: int, simultaneous_transfers: bool) -> None:
        """Initializer for the solver

        Args:
            time_start (timedelta): the start time of the schedule
            time_end (timedelta): the end time of the schedule
            time_max_gap (timedelta): the maximum gap between activities
            time_transfer (timedelta): the time needed for transferring between activities
            assessment_names (List[str]): the names of the assessments
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
        
        self.__clients_per_assessment = collections.defaultdict(list)
        self.__time_interval_vars_per_room = collections.defaultdict(list)
        self.__time_interval_vars_per_client = collections.defaultdict(list)
        self.__activity_bool_vars = collections.defaultdict(list)
        self.__last_activity_end_time_int_vars = []
        
        self.__activity_index_floor_bool_vars = dict()
        self.__activity_index_time_interval_vars = dict()
        self.__activity_index_start_time_int_vars = dict()
        self.__activity_index_end_time_int_vars = dict()
        self.__activity_index_room_bool_vars = dict()
        
        self.__activity_floor_bool_vars = dict()
        self.__activity_time_interval_vars = dict()
        self.__activity_start_time_int_vars = dict()
        self.__activity_end_time_int_vars = dict()

        self.__activity_precedence_bool_vars: Dict[Tuple[int, int, int], IntVar] = dict()
        self.__room_floor_bool_vars = dict()
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
    
    def __find_last_activity_condition(self, conditions: List[Condition], assessment: Assessment) -> Condition:
        """Helper function for finding the last activity condition

        Args:
            conditions (List[Condition]): the list of conditions

        Returns:
            Condition: the last activity condition
        """
        length_activities = len(assessment.activities)
        for condition in conditions:
            if condition.option == ActivityConditionOption.IN_FIXED_ORDER_AS and condition.args['order'] == length_activities - 1:
                return condition
        return None
    
    def __define_objective(self):
        """Helper function for defining the objective of the solver
        """
        assert len(self.__last_activity_end_time_int_vars) == sum([_assessment.quantity for _assessment in self.__assessments]), 'Invalid number of last activities'
        
        makespan = self.__model.NewIntVar(0, self.__horizon, 'makespan')
        self.__model.AddMaxEquality(makespan, self.__last_activity_end_time_int_vars)
    
    def __initialize_variables(self):
        """
        """
        previous_assessment_quantity = 0
        for assessment in self.__assessments:
            activities = [
                self.__activity_type(activity_room.duration, activity.id, activity_room.room.id, activity_room.room.floor)
                for activity in assessment.activities
                for activity_room in activity.rooms
            ]
            schedules = [[] for _ in assessment.activities]
                
            for activity in assessment.activities:
                for condition in activity.conditions:
                    if condition.option_type != ActivityConditionOptionType.ORDER:
                        continue
                    
                    order = int(condition.args.get('order', -1))
                    if order < 0:
                        raise ValueError('Invalid order argument provided')
                    
                    if condition.option == ActivityConditionOption.BEFORE:
                        order -= 1
                    elif condition.option == ActivityConditionOption.AFTER:
                        order += 1
                    
                    for activity_room in activity.rooms:
                        a = self.__activity_type(activity_room.duration, activity.id, activity_room.room.id, activity_room.room.floor)
                        schedules[int(order)].append(a)
                        activities.remove(a)
                    
            self.__schedules.extend(
                [[
                    schedule
                    if schedule
                    else activities
                    for schedule in schedules
                ]] * assessment.quantity
            )
            self.__clients_per_assessment[assessment.id].extend(list(range(previous_assessment_quantity, previous_assessment_quantity + assessment.quantity)))
            previous_assessment_quantity += assessment.quantity
    
    def __define_variables(self):
        """Helper function for defining the variables of the solver
        """
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
                    for activity in activities:
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
                        
                        self.__activity_index_room_bool_vars[(client_id, activity_index, activity.room_id)] = current_activity
                        self.__activity_bool_vars[(client_id, activity.id)].append(current_activity)
                        
                        self.__model.Add(start == current_start).OnlyEnforceIf(current_activity)
                        self.__model.Add(duration == current_duration).OnlyEnforceIf(current_activity)
                        self.__model.Add(end == current_end).OnlyEnforceIf(current_activity)
                        self.__model.Add(current_floor == activity.room_floor).OnlyEnforceIf(current_activity)
                        self.__model.Add(floor == current_floor).OnlyEnforceIf(current_activity)
                        
                        self.__activity_start_time_int_vars[(client_id, activity.id, activity_index)] = current_start
                        self.__activity_end_time_int_vars[(client_id, activity.id, activity_index)] = current_end
                        self.__activity_time_interval_vars[(client_id, activity.id, activity_index)] = current_interval
                        self.__activity_floor_bool_vars[(client_id, activity.id, activity_index)] = current_floor
                        
                    self.__model.AddExactlyOne(current_activities)
                else:
                    self.__model.Add(floor == activity.room_floor)
                    
                    self.__activity_start_time_int_vars[(client_id, activities[0].id, activity_index)] = start
                    self.__activity_end_time_int_vars[(client_id, activities[0].id, activity_index)] = end
                    self.__activity_time_interval_vars[(client_id, activities[0].id, activity_index)] = interval
                    self.__activity_floor_bool_vars[(client_id, activities[0].id, activity_index)] = floor
                    
                    self.__time_interval_vars_per_room[activities[0].room_id].append(interval)
                    self.__time_interval_vars_per_client[client_id].append(interval)
                    
                    self.__activity_index_room_bool_vars[(client_id, activity_index, activities[0].room_id)] = self.__model.NewConstant(1)
                    self.__activity_bool_vars[(client_id,  activities[0].id)].append(self.__model.NewConstant(1))                    
                
            self.__last_activity_end_time_int_vars.append(previous_end)
    
    def __apply_general_constraints(self):
        """
        """
        if not self.__simultaneous_transfers:
            self.__model.AddNoOverlap(self.__transfer_time_interval_vars.values())
        
        for client_id, _ in enumerate(self.__schedules):
            assessment = self.__get_assessment_by_client_id(client_id)
            for activity in assessment.activities:
                self.__model.AddExactlyOne(self.__activity_bool_vars[(client_id, activity.id)])
            
            self.__model.AddNoOverlap(self.__time_interval_vars_per_client[client_id])
            
            for activity_index, _ in enumerate(self.__schedules[client_id]):
                self.__model.AddModuloEquality(0, self.__activity_index_start_time_int_vars[(client_id, activity_index)], self.__time_max_interval)
                self.__model.AddModuloEquality(0, self.__activity_index_end_time_int_vars[(client_id, activity_index)], self.__time_max_interval)
    
    def __apply_gap_constraints(self):
        """Helper function for applying the gap constraints of the solver namely:
        
        - Gaps between activities
        - Transfers between activities at different floors
        """
        for client_id, schedule in enumerate(self.__schedules):
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
                    
                    # self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] - self.__activity_index_end_time_int_vars[(client_id, activity_index)] == duration).OnlyEnforceIf(floor)
                    self.__model.Add(start == self.__activity_index_end_time_int_vars[(client_id, activity_index)]).OnlyEnforceIf(floor)
                    self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] == end).OnlyEnforceIf(floor)
                    
                    self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] >= self.__activity_index_end_time_int_vars[(client_id, activity_index)]).OnlyEnforceIf(floor.Not())
                    self.__model.Add(self.__activity_index_start_time_int_vars[(client_id, other_activity_index)] - self.__activity_index_end_time_int_vars[(client_id, activity_index)] <= self.__time_max_gap).OnlyEnforceIf(floor.Not())
                    
                    self.__time_interval_vars_per_client[client_id].append(interval)
                    self.__transfer_start_time_int_vars[(client_id, activity_index, other_activity_index)] = start
                    self.__transfer_end_time_int_vars[(client_id, activity_index, other_activity_index)] = end
                    self.__transfer_time_interval_vars[(client_id, activity_index, other_activity_index)] = interval
    
    def __apply_precedence_constraints(self):
        """Helper function for applying the precedence constraints of the solver namely:
        
        - Maximum gap between activities
        - Transfer time between activities in different floors
        """
        for client_id, schedule in enumerate(self.__schedules):
            arcs = []
            for activity_index, _ in enumerate(schedule):
                first_activity = self.__model.NewBoolVar(f'{activity_index} is first')
                arcs.append((0, activity_index + 1, first_activity))
                
                last_activity = self.__model.NewBoolVar(f'{activity_index} is last')
                arcs.append((activity_index + 1, 0, last_activity))
                
                for other_activity_index, _ in enumerate(schedule):
                    if activity_index == other_activity_index:
                        continue
                    
                    next_activity = self.__model.NewBoolVar(f'{other_activity_index} is after {activity_index}')
                    self.__activity_precedence_bool_vars[(client_id, activity_index, other_activity_index)] = next_activity
                    arcs.append((activity_index + 1, other_activity_index + 1, next_activity))
                    
                    suffix = f'_trf_c{client_id}_a{activity_index}_a{other_activity_index}'
                    start = self.__model.NewIntVar(0, self.__horizon, f'start{suffix}')
                    duration = self.__time_transfer
                    end = self.__model.NewIntVar(0, self.__horizon, f'end{suffix}')
                    interval = self.__model.NewIntervalVar(start, duration, end, f'interval{suffix}')
                    floor = self.__model.NewBoolVar(f'floor{suffix}')
                    
                    self.__room_floor_bool_vars[(client_id, activity_index, other_activity_index)] = floor
                    
                    self.__model.AddModuloEquality(0, start, self.__time_max_interval)
                    self.__model.AddModuloEquality(0, end, self.__time_max_interval)
                    
                    self.__model.Add(self.__activity_index_floor_bool_vars[(client_id, activity_index)] != self.__activity_index_floor_bool_vars[(client_id, other_activity_index)]).OnlyEnforceIf(floor)
                    self.__model.Add(self.__activity_index_floor_bool_vars[(client_id, activity_index)] == self.__activity_index_floor_bool_vars[(client_id, other_activity_index)]).OnlyEnforceIf(floor.Not())
                    

                    self.__model.Add(start == self.__activity_index_end_time_int_vars[(client_id, activity_index)]).OnlyEnforceIf(floor, next_activity)
                    self.__model.Add(end == self.__activity_index_start_time_int_vars[(client_id, other_activity_index)]).OnlyEnforceIf(floor, next_activity)
                    
                    self.__model.Add(start >= self.__activity_index_end_time_int_vars[(client_id, activity_index)]).OnlyEnforceIf(floor.Not(), next_activity)
                    self.__model.Add(start - self.__activity_index_end_time_int_vars[(client_id, activity_index)] <= self.__time_max_gap).OnlyEnforceIf(floor.Not(), next_activity)
                    
                    self.__time_interval_vars_per_client[client_id].append(interval)
                    self.__transfer_start_time_int_vars[(client_id, activity_index, other_activity_index)] = start
                    self.__transfer_end_time_int_vars[(client_id, activity_index, other_activity_index)] = end
                    self.__transfer_time_interval_vars[(client_id, activity_index, other_activity_index)] = interval
            
            self.__model.AddCircuit(arcs)
    
    # Activity Conditions
    def __apply_before_activity_constraint(self, activity_id: int, other_activity_id: int, negate: bool = False):
        """[Activity Condition] Applies the condition that an activity must be before another activity; end time of activity <= start time of another activity. 

        Args:
            activity_id (int): the id of the activity
            before_activity_id (int): the id of the other acti vity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_before_time_constraint(self, activity_id: int, time_before: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be before a certain time; end time of activity <= time_before.

        Args:
            activity_id (int): the id of the activity
            time_before (int): the maximum time limit for the end of the activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_before_order_constraint(self, activity_id: int, order: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be before a certain order; end time of activity <= start time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        self.__apply_order_constraint(activity_id, order - 1, negate)
    
    def __apply_after_activity_constraint(self, activity_id: int, other_activity_id: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be after another activity; start time of activity >= end time of another activity.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_after_time_constraint(self, activity_id: int, time_after: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be after a certain time; start time of activity >= time_after.

        Args:
            activity_id (int): the id of the activity
            time_after (int): the minimum time limit for the start of the activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_after_order_constraint(self, activity_id: int, order: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be after a certain order; start time of activity >= end time of another activity at given order.

        Args:
            activity_id (int): the id of the activity
            order (int): the order of the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        self.__apply_order_constraint(activity_id, order + 1, negate)
    
    def __apply_right_after_activity_constraint(self, activity_id: int, other_activity_id: int, time_max_gap: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be right after another activity; start time of activity >= end time of another activity && start time of activity - end time of another activity <= time_max_gap.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_max_gap (int): the maximum time gap between the two activities
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_right_before_activity_constraint(self, activity_id: int, other_activity_id: int, time_max_gap: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be right before another activity; start time of activity <= end time of another activity && end time of another activity - start time of activity <= time_max_gap.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_max_gap (int): the maximum time gap between the two activities
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_between_activities_constraint(self, activity_id: int, other_activity_id_before: int, other_activity_id_after: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two other activities; start time of activity >= end time of another activity before && end time of activity <= start time of another activity after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id_before (int): the id of the other activity before
            other_activity_id_after (int): the id of the other activity after
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_between_times_constraint(self, activity_id: int, time_before: int, time_after: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two times; start time of activity >= time_before && end time of activity <= time_after.

        Args:
            activity_id (int): the id of the activity
            time_before (int): the minimum time limit for the start of the activity
            time_after (int): the maximum time limit for the end of the activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_between_orders_constraint(self, activity_id: int, order_before: int, order_after: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be between two orders; start time of activity >= end time of another activity at order_before && end time of activity <= start time of another activity at order_after.

        Args:
            activity_id (int): the id of the activity
            order_before (int): the order of the other activity before
            order_after (int): the order of the other activity after
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_within_after_activity_constraint(self, activity_id: int, other_activity_id: int, time_after: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be within a certain time after another activity; start time of activity >= end time of another activity && start time of activity <= end time of another activity + time_after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_after (int): the time limit after the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_within_before_activity_constraint(self, activity_id: int, other_activity_id: int, time_before: int, negate: bool):
        """[Activity Condition] Applies the condition that an activity must be within a certain time before another activity; start time of activity <= end time of another activity && start time of activity >= end time of another activity - time_after.

        Args:
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            time_before (int): the time limit before the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_order_constraint(self, activity_id: int, client: Client, order: int, negate: bool = False):
        """[Activity Condition] Applies the condition that an activity must be at a certain order; start time of activity >= end time of other activities at < order && end time of activity <= start time of other activities at > order.

        Args:
            activity_id (int): the id of the activity
            client_id (int): the id of the client
            order (int): the order of the activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    # Room Conditions
    def __apply_maximum_capacity_constraint(self, room_id: int, capacity: int, negate: bool):
        """[Room Condition] Applies the condition that a room must have a maximum capacity; sum of clients in room <= capacity.

        Args:
            room_id (int): the id of the room
            capacity (int): the maximum capacity of the room
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_unique_room_for_activity_constraint(self, activity_id: int, negate: bool):
        """[Room Condition] Applies the condition that an activity must be in a unique room; sum of activities in room <= 1.

        Args:
            activity_id (int): the id of the activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass
    
    def __apply_same_room_for_activities_constraint(self, client_id: int, room_id: int, activity_id: int, other_activity_id: int, negate: bool):
        """[Room Condition] Applies the condition that the two activities of client must be in the same room; room id of activity == room id of other activity.

        Args:
            client_id (int): the id of the client
            room_id (int): the id of the room
            activity_id (int): the id of the activity
            other_activity_id (int): the id of the other activity
            negate (bool): whether to generate or avoid generating the constraint
        """
        pass

    @property
    def assessments(self) -> List[Assessment]:
        """Getter attribute for the assessments
        """
        return self.__assessments
    
    @assessments.setter
    def assessments(self, _assessments: List[Assessment]) -> None:
        """Setter attribute for the assessments
        """
        self.__assessments = _assessments
    
    def __validate_assessment(self, _assessment: Assessment) -> bool:
        """Helper function for validating the assessments
        """
        if not getattr(_assessment, 'id', False):
            return False
        if not getattr(_assessment, 'name', False):
            return False
        if not getattr(_assessment, 'activities', False):
            return False
        if not getattr(_assessment, 'quantity', False):
            return False
        return True
    
    def generate(self):
        assert self.__assessments is not None, 'Invalid assessments'
        
        self.__initialize_variables()
        self.__define_variables()
        self.__apply_gap_constraints()
        self.__apply_general_constraints()
        self.__define_objective()
        
        self.__solver = cp_model.CpSolver()
        self.__status = self.__solver.Solve(self.__model)
        
        if self.__status != cp_model.OPTIMAL:
            return self.__solver.StatusName(self.__status)
        
        for client_id, schedule in enumerate(self.__schedules):
            print(f'Client {client_id}')
            a = []
            previous_activity_index = None
            for activity_index, activities in enumerate(schedule):
                if not previous_activity_index:
                    if self.__solver.Value(self.__room_floor_bool_vars[(client_id, previous_activity_index, activity_index)]):
                        a.append(('t', self.__solver.Value(self.__transfer_start_time_int_vars[(client_id, previous_activity_index, activity_index)])))
                for activity in activities:
                    if self.__solver.Value(self.__activity_index_room_bool_vars[(client_id, activity_index, activity.room_id)]):
                        a.append((activity.id, self.__solver.Value(self.__activity_index_start_time_int_vars[(client_id, activity_index)])))
                        break
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
    NUM_OPT_CLIENTS = 4

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
            floor=1,
            conditions=[
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    mandatory=True,
                    args=dict(activity_id=201)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    mandatory=True,
                    args=dict(activity_id=208)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.UNIQUE,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    mandatory=True,
                    args=dict(activity_id=211)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.SAME,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    mandatory=True,
                    args=dict(activity_ids=[201, 208, 211])
                )
            ]
        ) for i in range(BASE_ROOM_ID + 1, BASE_ROOM_ID + NUM_CLIENT_ROOMS + 1)
    ]
    PHLEBOTOMY_ROOMS = [
        Room(
            id=i,
            name=f'Client Room {i}',
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_6 + 1, BASE_ROOM_ID + SUM_7 + 1)
    ]
    CONSULTATION_ROOMS = [
        Room(
            id=i,
            name=f'Consultation Room {i}',
            floor=2,
            conditions=[
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.MAXIMUM,
                    option_type=RoomConditionOptionType.CLIENT,
                    mandatory=True,
                    args=dict(max_clients=3)
                ),
                Condition(
                    scope=ConditionScope.ROOM,
                    option=RoomConditionOption.SAME,
                    option_type=RoomConditionOptionType.ACTIVITY,
                    mandatory=True,
                    args=dict(activity_ids=[203, 210])
                )
            ]
        ) for i in range(BASE_ROOM_ID + SUM_4 + 1, BASE_ROOM_ID + SUM_5 + 1)
    ]
    CARDIAC_ROOMS = [
        Room(
            id=i,
            name=f'Cardiac Room {i}',
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_3 + 1, BASE_ROOM_ID + SUM_4 + 1)
    ]
    MRI_ROOMS = [
        Room(
            id=i,
            name=f'MRI Room {n}',
            floor=2,
            conditions=[]
        ) for i, n in zip(range(BASE_ROOM_ID + SUM_1 + 1, BASE_ROOM_ID + SUM_2 + 1), [*(['1.5T'] * NUM_MRI_15_ROOMS), *(['3T'] * NUM_MRI_3_ROOMS)])
    ]
    ULTRASOUND_ROOMS = [
        Room(
            id=i,
            name=f'Ultrasound Room {i}',
            floor=2,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + NUM_CLIENT_ROOMS + 1, BASE_ROOM_ID + SUM_1 + 1)
    ]
    EYES_EARS_ROOMS = [
        Room(
            id=i,
            name=f'Eyes and Ears Room {i}',
            floor=1,
            conditions=[]
        ) for i in range(BASE_ROOM_ID + SUM_5 + 1, BASE_ROOM_ID + SUM_6 + 1)
    ]
    RADIOLOGY_ROOMS = [
        Room(
            id=i,
            name=f'Radiology Room {i}',
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
                            mandatory=True,
                            args=dict(order=0)
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
                            mandatory=True,
                            args=dict(order=1)
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
                            mandatory=True,
                            args=dict(other_activity_id=205)
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
                            mandatory=True,
                            args=dict(time_before=timedelta(hours=16))
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
                            mandatory=True,
                            args=dict(other_activity_id=208)
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
                            mandatory=True,
                            args=dict(other_activity_id=206)
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
                            mandatory=True,
                            args=dict(time_after=timedelta(hours=13))
                        ),
                        Condition(
                            scope=ConditionScope.ACTIVITY,
                            option=ActivityConditionOption.AFTER,
                            option_type=ActivityConditionOptionType.ACTIVITY,
                            mandatory=True,
                            args=dict(other_activity_id=205)
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
                            mandatory=True,
                            args=dict(order=9)
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
                            mandatory=True,
                            args=dict(order=10)
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