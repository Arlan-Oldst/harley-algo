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
            'totalMale': 4,
            'totalFemale': 4,
            'allow_simultaneous_transfers': False,
            'data': {
                'clientElite': {
                    'singleMale': 4,
                    'singleFemale': 4,
                },
                'clientUltimate': {
                    'singleMale': 0,
                    'singleFemale': 0,
                }
            }
        },
        'rooms': [
            {
                'id': 'Belgrave',
                'name': 'Belgrave',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Belgrave',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Belgrave',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Belgrave',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Bloomsbury',
                'name': 'Bloomsbury',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Bloomsbury',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Bloomsbury',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Bloomsbury',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Cavendish',
                'name': 'Cavendish',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Cavendish',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Cavendish',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Cavendish',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Claremont',
                'name': 'Claremont',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Claremont',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Claremont',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Claremont',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Grosvenor',
                'name': 'Grosvenor',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Grosvenor',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Grosvenor',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Grosvenor',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Sloane',
                'name': 'Sloane',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Sloane',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Sloane',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Sloane',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Soho',
                'name': 'Soho',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Soho',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Soho',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Soho',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'St James',
                'name': 'St James',
                'floor': 1,
                'type': 'CLIENT',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'UNIQUE',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'St James',
                            'activity_id': 'Check-in, Consent & Change',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'St James',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Lunch',
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'St James',
                            'activity_id': 'Check-in, Consent & Change',
                            'other_activity_id': 'Checkout',
                            'generate': True
                        }
                    },
                ]
            },
            {
                'id': 'Phlebotomy Room 1',
                'name': 'Phlebotomy Room 1',
                'floor': 1,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Doctor Room 1',
                'name': 'Doctor Room 1',
                'floor': 2,
                'type': 'OTHER',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 1',
                            'activity_id': 'First Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 1',
                            'activity_id': 'Final Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Doctor Room 1',
                            'activity_id': 'First Consultation',
                            'other_activity_id': 'Final Consultation',
                            'generate': True
                        }
                    }
                ]
            },
            {
                'id': 'Doctor Room 2',
                'name': 'Doctor Room 2',
                'floor': 2,
                'type': 'OTHER',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 2',
                            'activity_id': 'First Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 2',
                            'activity_id': 'Final Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Doctor Room 2',
                            'activity_id': 'First Consultation',
                            'other_activity_id': 'Final Consultation',
                            'generate': True
                        }
                    }
                ]
            },
            {
                'id': 'Doctor Room 3',
                'name': 'Doctor Room 3',
                'floor': 2,
                'type': 'OTHER',
                'conditions': [
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 3',
                            'activity_id': 'First Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'MAXIMUM',
                        'optionType': 'CLIENT',
                        'args': {
                            'room_id': 'Doctor Room 3',
                            'activity_id': 'Final Consultation',
                            'capacity': 3,
                            'generate': True
                        }
                    },
                    {
                        'scope': 'ROOM',
                        'option': 'SAME',
                        'optionType': 'ACTIVITY',
                        'args': {
                            'room_id': 'Doctor Room 3',
                            'activity_id': 'First Consultation',
                            'other_activity_id': 'Final Consultation',
                            'generate': True
                        }
                    }
                ]
            },
            {
                'id': 'Cardiac Room 1',
                'name': 'Cardiac Room 1',
                'floor': 1,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Cardiac Room 2',
                'name': 'Cardiac Room 2',
                'floor': 1,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'MRI Room 1.5T',
                'name': 'MRI Room 1.5T',
                'floor': 2,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'MRI Room 3T',
                'name': 'MRI Room 3T',
                'floor': 2,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Ultrasound Room 1',
                'name': 'Ultrasound Room 1',
                'floor': 2,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Ultrasound Room 2',
                'name': 'Ultrasound Room 2',
                'floor': 2,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Eyes & Ears Room 1',
                'name': 'Eyes & Ears Room 1',
                'floor': 1,
                'type': 'OTHER',
                'conditions': []
            },
            {
                'id': 'Radiology Room 1',
                'name': 'Radiology Room 1',
                'floor': 2,
                'type': 'OTHER',
                'conditions': []
            }
        ],
        'assessments': [
            {
                'id': 'Ultimate',
                'name': 'Ultimate',
                'activities': [
                    {
                        'id': 'Check-in, Consent & Change',
                        'name': 'Check-in, Consent & Change',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Check-in, Consent & Change',
                                    'order': 0,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 10,
                            'Bloomsbury': 10,
                            'Cavendish': 10,
                            'Claremont': 10,
                            'Grosvenor': 10,
                            'Sloane': 10,
                            'Soho': 10,
                            'St James': 10,
                        }
                    },
                    {
                        'id': 'Bloods & Obs',
                        'name': 'Bloods & Obs',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Bloods & Obs',
                                    'order': 1,
                                    'generate': True
                                }
                            },
                            {
                                'scope': 'ACTIVITY',
                                'option': 'WITHIN_AFTER',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Bloods & Obs',
                                    'other_activity_id': 'Check-in, Consent & Change',
                                    'time_after': '00:30:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Phlebotomy Room 1': 10,
                        }
                    },
                    {
                        'id': 'First Consultation',
                        'name': 'First Consultation',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'First Consultation',
                                    'other_activity_id': 'MRI',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Doctor Room 1': 60,
                            'Doctor Room 2': 60,
                            'Doctor Room 3': 60,
                        }
                    },
                    {
                        'id': 'Stress Echo',
                        'name': 'Stress Echo',
                        'conditions': [],
                        'rooms': {
                            'Cardiac Room 1': 50,
                            'Cardiac Room 2': 50,
                        }
                    },
                    {
                        'id': 'MRI',
                        'name': 'MRI',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'MRI',
                                    'time_before': '16:00:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'MRI Room 1.5T': 80,
                            'MRI Room 3T': 20,
                        }
                    },
                    {
                        'id': 'Ultrasound',
                        'name': 'Ultrasound',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Ultrasound',
                                    'other_activity_id': 'Lunch',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Ultrasound Room 1': 60,
                            'Ultrasound Room 2': 60,
                        }
                    },
                    {
                        'id': 'Eyes & Ears',
                        'name': 'Eyes & Ears',
                        'conditions': [],
                        'rooms': {
                            'Eyes & Ears Room 1': 10,
                        }
                    },
                    {
                        'id': 'Lunch',
                        'name': 'Lunch',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BETWEEN',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'Lunch',
                                    'time_before': '11:00:00',
                                    'time_after': '16:00:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 30,
                            'Bloomsbury': 30,
                            'Cavendish': 30,
                            'Claremont': 30,
                            'Grosvenor': 30,
                            'Sloane': 30,
                            'Soho': 30,
                            'St James': 30,
                        }
                    },
                    {
                        'id': 'Radiologist Consult',
                        'name': 'Radiologist Consult',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'AFTER',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'Radiologist Consult',
                                    'time_after': '13:00:00',
                                    'generate': True
                                }
                            },
                            {
                                'scope': 'ACTIVITY',
                                'option': 'AFTER',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Radiologist Consult',
                                    'other_activity_id': 'MRI',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Radiology Room 1': 25,
                        }
                    },
                    {
                        'id': 'Final Consultation',
                        'name': 'Final Consultation',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Final Consultation',
                                    'order': 9,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Doctor Room 1': 30,
                            'Doctor Room 2': 30,
                            'Doctor Room 3': 30,
                        }
                    },
                    {
                        'id': 'Checkout',
                        'name': 'Checkout',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Checkout',
                                    'order': 10,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 10,
                            'Bloomsbury': 10,
                            'Cavendish': 10,
                            'Claremont': 10,
                            'Grosvenor': 10,
                            'Sloane': 10,
                            'Soho': 10,
                            'St James': 10,
                        }
                    },
                ],
            },
            {
                'id': 'Elite',
                'name': 'Elite',
                'activities': [
                    {
                        'id': 'Check-in, Consent & Change',
                        'name': 'Check-in, Consent & Change',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Check-in, Consent & Change',
                                    'order': 0,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 10,
                            'Bloomsbury': 10,
                            'Cavendish': 10,
                            'Claremont': 10,
                            'Grosvenor': 10,
                            'Sloane': 10,
                            'Soho': 10,
                            'St James': 10,
                        }
                    },
                    {
                        'id': 'Bloods & Obs',
                        'name': 'Bloods & Obs',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Bloods & Obs',
                                    'order': 1,
                                    'generate': True
                                }
                            },
                            {
                                'scope': 'ACTIVITY',
                                'option': 'WITHIN_AFTER',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Bloods & Obs',
                                    'other_activity_id': 'Check-in, Consent & Change',
                                    'time_after': '00:30:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Phlebotomy Room 1': 10,
                        }
                    },
                    {
                        'id': 'First Consultation',
                        'name': 'First Consultation',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'First Consultation',
                                    'other_activity_id': 'MRI',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Doctor Room 1': 60,
                            'Doctor Room 2': 60,
                            'Doctor Room 3': 60,
                        }
                    },
                    {
                        'id': 'Stress Echo',
                        'name': 'Stress Echo',
                        'conditions': [],
                        'rooms': {
                            'Cardiac Room 1': 50,
                            'Cardiac Room 2': 50,
                        }
                    },
                    {
                        'id': 'MRI',
                        'name': 'MRI',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'MRI',
                                    'time_before': '16:00:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'MRI Room 1.5T': 75,
                            'MRI Room 3T': 90,
                        }
                    },
                    {
                        'id': 'Ultrasound',
                        'name': 'Ultrasound',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BEFORE',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Ultrasound',
                                    'other_activity_id': 'Lunch',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Ultrasound Room 1': 60,
                            'Ultrasound Room 2': 60,
                        }
                    },
                    {
                        'id': 'Eyes & Ears',
                        'name': 'Eyes & Ears',
                        'conditions': [],
                        'rooms': {
                            'Eyes & Ears Room 1': 10,
                        }
                    },
                    {
                        'id': 'Lunch',
                        'name': 'Lunch',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'BETWEEN',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'Lunch',
                                    'time_before': '11:00:00',
                                    'time_after': '16:00:00',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 30,
                            'Bloomsbury': 30,
                            'Cavendish': 30,
                            'Claremont': 30,
                            'Grosvenor': 30,
                            'Sloane': 30,
                            'Soho': 30,
                            'St James': 30,
                        }
                    },
                    {
                        'id': 'Radiologist Consult',
                        'name': 'Radiologist Consult',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'AFTER',
                                'optionType': 'TIME',
                                'args': {
                                    'activity_id': 'Radiologist Consult',
                                    'time_after': '13:00:00',
                                    'generate': True
                                }
                            },
                            {
                                'scope': 'ACTIVITY',
                                'option': 'AFTER',
                                'optionType': 'ACTIVITY',
                                'args': {
                                    'activity_id': 'Radiologist Consult',
                                    'other_activity_id': 'MRI',
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Radiology Room 1': 15,
                        }
                    },
                    {
                        'id': 'Final Consultation',
                        'name': 'Final Consultation',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Final Consultation',
                                    'order': 9,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Doctor Room 1': 30,
                            'Doctor Room 2': 30,
                            'Doctor Room 3': 30,
                        }
                    },
                    {
                        'id': 'Checkout',
                        'name': 'Checkout',
                        'conditions': [
                            {
                                'scope': 'ACTIVITY',
                                'option': 'IN_FIXED_ORDER_AS',
                                'optionType': 'ORDER',
                                'args': {
                                    'activity_id': 'Checkout',
                                    'order': 10,
                                    'generate': True
                                }
                            }
                        ],
                        'rooms': {
                            'Belgrave': 10,
                            'Bloomsbury': 10,
                            'Cavendish': 10,
                            'Claremont': 10,
                            'Grosvenor': 10,
                            'Sloane': 10,
                            'Soho': 10,
                            'St James': 10,
                        }
                    },
                ],
            },
        ]
    }
    handler(event, None)