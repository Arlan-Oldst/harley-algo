"""Module for handling database connections.

Assumptions:
 - The database is DynamoDB
"""
import os
import requests
from src.models.model import Assessment, Condition, Activity, GeneralCondition, Resource
from src.utils.serializer import serialize_as_dataclass
from typing import List

def retrieve_assessments(authorization) -> List[Assessment]:
    """Retrieve all assessments from the database.
    """
    url = os.environ.get('NX_API_URL_ASSESSMENT')
    endpoint = 'get-all'
    response = requests.get(f'{url}/{endpoint}', headers={'Authorization': authorization})
    
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve assessments. Error: {response.reason}')
    
    return [
        serialize_as_dataclass(Assessment, **data)
        for data in response.json()
    ]

def retrieve_resources(authorization) -> List[Resource]:
    """Retrieve all resources from the database.
    """
    url = os.environ.get('NX_API_URL_RESOURCE')
    endpoint = 'get-all'
    response = requests.get(f'{url}/{endpoint}', headers={'Authorization': authorization})
    
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve resources. Error: {response.reason}')
    
    return [
        serialize_as_dataclass(Resource, **data)
        for data in response.json()
    ]

def retrieve_activity_conditions_by_assessment_id(authorization, assessment_id) -> List[Condition]:
    """Retrieve activity conditions by assessment from the database.
    """
    url = os.environ.get('NX_API_URL_ACTIVITY')
    endpoint = f'condition/get-all/{assessment_id}'
    response = requests.get(f'{url}/{endpoint}', headers={'Authorization': authorization})
    
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve conditions. Error: {response.reason}')
    
    return [
        serialize_as_dataclass(Condition, **data)
        for data in response.json()
    ]

def retrieve_general_conditions(authorization) -> List[GeneralCondition]:
    """Retrieve all general conditions from the database.
    """
    url = os.environ.get('NX_API_URL_ACTIVITY')
    endpoint = 'general-conditions/get-all'
    response = requests.get(f'{url}/{endpoint}', headers={'Authorization': authorization})
    
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve general conditions. Error: {response.reason}')
    
    return response.json()

def retrieve_activities(authorization: str) -> List[Activity]:
    """Retrieve all activities from the database.
    """
    url = os.environ.get('NX_API_URL_ACTIVITY')
    endpoint = 'activity/get-all'
    response = requests.get(f'{url}/{endpoint}', headers={'Authorization': authorization})
    
    if response.status_code != 200:
        raise Exception(f'Failed to retrieve assessment activities. Error: {response.reason}')
    
    return [
        serialize_as_dataclass(Activity, **data)
        for data in response.json()
    ]