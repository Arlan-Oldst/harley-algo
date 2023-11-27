"""Helper functions for structuring and validating JSON data.

Assumptions:
 - All data is valid JSON
"""
import types
from typing import List, get_origin
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

def serialize_condition(condition: m.Condition) -> sm.Condition:
    pass

def serialize_room(room: m.Resource) -> sm.Room:
    pass

def serialize_activity_room() -> sm.ActivityRoom:
    pass

def serialize_activity(activity: m.Activity) -> sm.Activity:
    pass

def serialize_assessment(**kwargs) -> sm.Assessment:
    # TODO: Modify to support m.Assessment instead
    return sm.Assessment(
        id=kwargs.get('id'),
        name=kwargs.get('name'),
        activities=kwargs.get('activities'),
    )

def serialize_assessments(scenario_action_data: m.ScenarioActionData, assessments: List[dict]) -> List[sm.Assessment]:
    # TODO: Modify to support m.Assessment instead
    num_elites = sum((scenario_action_data.client_elite.single_female, scenario_action_data.client_elite.single_male))
    num_ultimates = sum((scenario_action_data.client_ultimate.single_female, scenario_action_data.client_ultimate.single_male))
    return [
        serialize_as_dataclass(sm.Assessment, **{**assessment, 'quantity': num_elites if assessment.get('name') == 'Elite' else num_ultimates})
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