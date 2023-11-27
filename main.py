"""The main handler function of the Lambda instance.

Assumptions:
 - The Lambda instance is running Python 3.11
 - The Lambda instance is triggered by SQS
 - The SQS message only contains the ScenarioAction ID
"""
from src.controllers.controller import Controller
import json

# def handler(event, context):
#     record: dict
#     for record in event['Records']:
#         print(f'Record {record}')
#         scenario_action_id = record.get('scenarioActionId', None)
        
#         assert scenario_action_id is not None, 'ScenarioAction ID is missing from SQS message'
        
#         return Controller.retrieve_generated_scenario(scenario_action_id)
        
def handler(event, context):
    return Controller.retrieve_generated_scenario(**event)

if __name__ == '__main__':
    event = {
        'scenarioAction': {
            'scenarioActionId': 'scenarioActionId',
            'firstClientArrivalTime': '07:15:00',
            'doctorsOnDuty': 3,
            'maxGap': 5,
            'totalMale': 2,
            'totalFemale': 2,
            'allow_simultaneous_transfers': False,
            'data': {
                'clientElite': {
                    'singleMale': 1,
                    'singleFemale': 1,
                },
                'clientUltimate': {
                    'singleMale': 1,
                    'singleFemale': 1,
                }
            }
        },
        'assessments': [
            {
                'id': 101,
                'name': 'Elite',
                'activities': [
                    {
                        'id': 201,
                        'name': 'Test',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 201,
                                    'order': 0,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': [
                            {
                                'room': {
                                    'id': 301,
                                    'name': 'Test',
                                    'floor': 1,
                                    'conditions': []
                                },
                                'duration': 30
                            }
                        ]
                    }
                ],
            },
            # {
            #     'id': 102,
            #     'name': 'Ultimate',
            #     'activities': [],
            # }
        ]
    }
    handler(event, None)