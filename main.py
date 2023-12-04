"""The main handler function of the Lambda instance.

Assumptions:
 - The Lambda instance is running Python 3.11
 - The Lambda instance is triggered by SQS
 - The SQS message only contains the ScenarioAction ID
"""
from src.controllers.controller import Controller
from flask import Flask
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def get_healthcheck():
    return 'OK', 200

@app.route('/', methods=['GET'])
def get_schedule(event):
    event = json.loads(event)
    return Controller.retrieve_generated_scenario(**event), 200

# def handler(event, context):
#     record: dict
#     for record in event['Records']:
#         print(f'Record {record}')
#         scenario_action_id = record.get('scenarioActionId', None)
        
#         assert scenario_action_id is not None, 'ScenarioAction ID is missing from SQS message'
        
#         return Controller.retrieve_generated_scenario(scenario_action_id)
        
# def handler(event, context):
#     return Controller.retrieve_generated_scenario(**event)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')