"""Helper functions for structuring and validating JSON data.

Assumptions:
 - All data is valid JSON
"""
import types
from typing import List, get_origin, Dict, Any, Tuple
from src.models import model as m
from src.models import solver_model as sm
from dataclasses import fields as fs
from datetime import timedelta, datetime
import re

def serialize_as_dataclass(o: object, **kwargs) -> object:
    field_types = {field.name: field.type for field in fs(o)}
    fields = list(kwargs.keys())
    attributes = dict()
    for field in fields:
        formatted_field = format_field(field)
        field_type = field_types.get(formatted_field, None)
        
        if field_type is None:
            continue
        
        attribute = kwargs.get(field, None)
        
        if attribute is None:
            continue
        
        if isinstance(field_type, types.UnionType):
            _types = field_type.__args__
            for _type in _types:
                try:
                    if _type is None:
                        attribute = None
                        continue
                    attribute = _type(attribute)
                    break
                except:
                    continue
        elif get_origin(field_type) is list:
            _type = field_type.__args__[0]
            attribute = [serialize_as_dataclass(_type, **a) for a in attribute]
        elif field_type in m.MODELS or field_type in sm.MODELS:
            attribute = serialize_as_dataclass(field_type, **attribute)
        else:
            attribute = field_type(attribute)
            
        attributes[formatted_field] = attribute
    
    return o(**attributes)

def serialize_scenario_action_as_solver_args(scenario_action: m.ScenarioAction) -> dict:
    solver_args = dict()
    
    first_client_arrival_time = datetime.strptime(scenario_action.first_client_arrival_time,"%H:%M:%S")
    solver_args['time_start'] = timedelta(hours=first_client_arrival_time.hour, minutes=first_client_arrival_time.minute, seconds=first_client_arrival_time.second)
    
    solver_args['time_end'] = timedelta(hours=23, minutes=59, seconds=59)
    
    solver_args['time_max_interval'] = timedelta(minutes=5)
    
    max_gap = timedelta(minutes=int(scenario_action.max_gap))
    solver_args['time_max_gap'] = max_gap
    
    solver_args['time_transfer'] = timedelta(minutes=5)
    
    solver_args['num_floors'] = 2
    
    doctors_on_duty = int(scenario_action.doctors_on_duty)
    solver_args['num_doctors'] = doctors_on_duty
    
    allow_simultaneous_transfers = bool(scenario_action.allow_simultaneous_transfers)
    solver_args['simultaneous_transfers'] = allow_simultaneous_transfers  
    
    return solver_args

def serialize_condition(**kwargs) -> sm.Condition:
    args = {
        arg: value if 'time' not in arg else datetime.strptime(value,"%H:%M:%S")
        for arg, value in kwargs.get('args').items()
    }
    kwargs = {
        **kwargs,
        'args': {
            arg: value if 'time' not in arg else timedelta(hours=value.hour, minutes=value.minute, seconds=value.second)
            for arg, value in args.items()
        }
    }
    return sm.Condition(
        **format_fields(kwargs),
    )

def serialize_conditions(conditions: List[dict]) -> List[sm.Condition]:
    return [
        serialize_condition(**condition)
        for condition in conditions
    ]

def serialize_room(**kwargs) -> sm.Room:
    # TODO: Modify to support m.Resource instead
    kwargs = {
        **kwargs,
        'conditions': serialize_conditions(kwargs.get('conditions'))
    }
    return sm.Room(
        **format_fields(kwargs),
    )

def serialize_rooms(rooms: List[dict]) -> List[sm.Room]:
    # TODO: Modify to support m.Resource instead
    return [
        serialize_room(**room)
        for room in rooms
    ]

def serialize_activity_room(r: List[sm.Room], room_id: str, duration: int) -> sm.ActivityRoom:
    # TODO: Modify to support m.Resource instead
    return sm.ActivityRoom(
        room=find_room(room_id, r),
        duration=duration
    )

def serialize_activity_rooms(r: List[sm.Room], activity_rooms: Dict[str, int]) -> List[sm.ActivityRoom]:
    # TODO: Modify to support m.Resource instead
    return [
        serialize_activity_room(r, room_id, duration)
        for room_id, duration in activity_rooms.items()
    ]

def serialize_activity(r: List[sm.Room], **kwargs) -> sm.Activity:
    # TODO: Modify to support m.Activity instead
    kwargs = {
        **kwargs,
        'conditions': serialize_conditions(kwargs.get('conditions')),
        'rooms': serialize_activity_rooms(r, kwargs.get('rooms'))
    }
    return sm.Activity(
        **format_fields(kwargs)
    )

def serialize_activities(r: List[sm.Room], activities: List[dict]) -> List[sm.Activity]:
    # TODO: Modify to support m.Activity instead
    return [
        serialize_activity(r, **activity)
        for activity in activities
    ]

def serialize_assessment(r: List[sm.Room], **kwargs) -> sm.Assessment:
    # TODO: Modify to support m.Assessment instead
    kwargs = {
        **kwargs,
        'activities': serialize_activities(r, kwargs.get('activities')),
    }
    return sm.Assessment(
        **format_fields(kwargs),
    )

def serialize_assessments(scenario_action_data: m.ScenarioActionData, r: List[sm.Room], assessments: List[dict]) -> List[sm.Assessment]:
    # TODO: Modify to support m.Assessment instead
    num_elites = sum((scenario_action_data.client_elite.single_female, scenario_action_data.client_elite.single_male))
    num_ultimates = sum((scenario_action_data.client_ultimate.single_female, scenario_action_data.client_ultimate.single_male))
    return [
        serialize_assessment(r, **{**assessment, 'quantity': num_elites})
        if 'elite' in str(assessment.get('name')).lower()
        else serialize_assessment(r, **{**assessment, 'quantity': num_ultimates})
        for assessment in assessments
    ]

def serialize_client(**kwargs) -> sm.Client:
    return sm.Client(
        id=kwargs.get('i'),
        assessment=kwargs.get('assessment')
    )

def serialize_clients(scenario_action_data: m.ScenarioActionData) -> sm.Client:
    # TODO: Add support for couples
    num_elites = sum(scenario_action_data.client_elite.single_female, scenario_action_data.client_elite.single_male)
    num_ultimates = sum(scenario_action_data.client_ultimate.single_female, scenario_action_data.client_ultimate.single_male)
    
def format_field(key: str) -> str:
    return re.sub(r'[A-Z]', repl=lambda match: f'_{str(match.group(0)).lower()}', string=key)

def format_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    return {
        format_field(field): value
        for field, value in fields.items()
    }

def find_room(room_id: str, rooms: List[sm.Room]) -> sm.Room:
    return next(filter(lambda room: room.id == room_id, rooms), None)