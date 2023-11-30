"""Controller module of the Lambda instance.

Functions:
 - Calls database helper functions
 - Calls serializer helper functions
 - Calls the scheduler
 - Returns output
"""
from src.utils.serializer import serialize_as_dataclass, serialize_scenario_action_as_solver_args, serialize_assessments, serialize_rooms
from src.models.model import ScenarioAction
from src.utils.solver import Solver
import json

class Controller:
    @staticmethod
    def retrieve_generated_scenario(**kwargs) -> dict:
        """Retrieve the generated scenario by the scheduler module."""
        # TODO: retrieve scenario action from database
        
        scenario_action: ScenarioAction = serialize_as_dataclass(ScenarioAction, **kwargs.get('scenarioAction'))
                
        solver_args = serialize_scenario_action_as_solver_args(scenario_action)
        solver = Solver(**solver_args)
        
        # TODO: set assessments attribute of Solver
        assessments = kwargs.get('assessments')
        r = serialize_rooms(kwargs.get('rooms'))
        solver.assessments = serialize_assessments(scenario_action.data, r, assessments)
        
        # TODO: generate scenario
        generated_scenario = solver.generate()
        
        # TODO: instantiate GeneratedScenario
        
        # TODO: jsonify GeneratedScenario
        
        # TODO: return JSON
        return json.dumps(generated_scenario)
        