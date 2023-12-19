"""The main handler function of the Lambda instance.

Assumptions:
 - The Lambda instance is running Python 3.11
 - The Lambda instance is triggered by SQS
 - The SQS message only contains the ScenarioAction ID
"""
from src.controllers.controller import Controller
from flask import Flask, request
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def get_healthcheck():
    return 'OK', 200

@app.route('/generate-senario', methods=['POST'])
def get_schedule():
    try:
        authorization = request.headers.get('Authorization', None)
        if authorization is None:
            raise Exception('Authorization header is missing.')
        
        event = request.get_json()
        return Controller.retrieve_generated_scenario(authorization, **event), 200
    except Exception:
        error = traceback.format_exc()
        print(error)
        return [error], 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')