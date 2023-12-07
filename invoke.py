from src.controllers.controller import Controller
import json

if __name__ == '__main__':
    with open('event_v2.json', 'r') as f:
        event = json.load(f)
        print(Controller.retrieve_generated_scenario(**event))