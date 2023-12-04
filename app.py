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