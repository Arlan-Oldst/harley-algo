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
    import json
    event = None
    with open('event.json', 'r') as jsonfile:
        event = json.load(jsonfile)
    print(handler(event, None))