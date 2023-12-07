"""Controller module of the Lambda instance.

Functions:
 - Calls database helper functions
 - Calls serializer helper functions
 - Calls the scheduler
 - Returns output
"""
from src.utils.serializer import serialize_as_dataclass, serialize_scenario_action_as_solver_args, serialize_assessments, serialize_rooms
from src.models.model import ScenarioAction
from src.utils.solver_v2 import Solver
import json

class Controller:
    @staticmethod
    def retrieve_generated_scenario(**kwargs) -> dict:
        """Retrieve the generated scenario by the scheduler module."""
        # TODO: retrieve scenario action from database
        
        solver = Solver()
        solver.scenario_action = kwargs.get('scenario_action')
        solver.resources = kwargs.get('resources')
        solver.assessments = kwargs.get('assessments')
        solver.activities = kwargs.get('activities')
        
        # TODO: set assessments attribute of Solver
        # assessments = kwargs.get('assessments')
        # r = serialize_rooms(kwargs.get('rooms'))
        # solver.assessments = serialize_assessments(scenario_action.data, r, assessments)
        
        # TODO: generate scenario
        generated_scenario = solver.generate()
        
        # TODO: instantiate GeneratedScenario
        
        # TODO: jsonify GeneratedScenario
        
        # TODO: return JSON
        return json.dumps(generated_scenario)
        