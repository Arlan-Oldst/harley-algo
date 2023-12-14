"""Controller module of the Lambda instance.

Functions:
 - Calls database helper functions
 - Calls serializer helper functions
 - Calls the scheduler
 - Returns output
"""
from src.utils.db import retrieve_assessments, retrieve_activity_conditions_by_assessment_id, retrieve_resources, retrieve_activities
from src.models.model import ScenarioAction
from src.utils.solver_v2 import Solver
from src.utils.serializer import serialize_as_dataclass
import collections
import json
import re

class Controller:
    @staticmethod
    def retrieve_generated_scenario(authorization, **kwargs) -> dict:
        """Retrieve the generated scenario by the scheduler module."""
        scenario_action = serialize_as_dataclass(ScenarioAction, **kwargs)
        
        activities = retrieve_activities(authorization)
        activity_ids_map = dict()
        activity_names_map = collections.defaultdict(list)
        for activity in activities:
            activity_names_map[activity.activity_name].append(activity)
            activity_ids_map[activity.activity_id] = activity
        
        assessments = retrieve_assessments(authorization)
        
        assessments = [assessment for assessment in assessments if assessment.enabled]
        assessment_names = [assessment.assessment_name for assessment in assessments if assessment.enabled]
        
        
        for assessment in assessments:
            if not assessment.enabled:
                continue
            
            activity_conditions = retrieve_activity_conditions_by_assessment_id(authorization, assessment.assessment_id)
            assessment.data['activity_conditions'] = activity_conditions
            
            other_names = [name for name in assessment_names if name != assessment.assessment_name]
            pattern = f'({"|".join(other_names)})'
            assessment.data['activities'] = [
                activity_names_map[activity_name]
                for activity_name in activity_names_map
                if re.search(
                    pattern,
                    activity_name,
                    re.IGNORECASE
                ) is None
            ]
                
        resources = retrieve_resources(authorization)
        
        solver = Solver()
        solver.resources = resources
        solver.assessments = assessments
        solver.activities = activities
        solver.activities_names_map = activity_names_map
        solver.scenario_action = scenario_action
        
        # # TODO: set assessments attribute of Solver
        # # assessments = kwargs.get('assessments')
        # # r = serialize_rooms(kwargs.get('rooms'))
        # # solver.assessments = serialize_assessments(scenario_action.data, r, assessments)
        
        # # TODO: generate scenario
        generated_scenario = solver.generate()
        
        # # TODO: instantiate GeneratedScenario
        
        # # TODO: jsonify GeneratedScenario
        
        # # TODO: return JSON
        return json.dumps(generated_scenario)