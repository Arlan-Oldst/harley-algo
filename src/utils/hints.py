from datetime import timedelta
from src.models.model import Assessment

HINTS = {
    (
        3, # Number of single Optimal
        0, # Number of couple Optimal
        5, # Number of single Ultimate
        0, # Number of couple Ultimate
        0, # Number of single Core
        0, # Number of couple Core
    ): {
        'Check-in, Consent & Change': [
            timedelta(hours=7, minutes=15),
            timedelta(hours=7, minutes=45),
            timedelta(hours=8, minutes=10),
            timedelta(hours=8, minutes=20),
            timedelta(hours=9, minutes=00),
            timedelta(hours=9, minutes=45),
            timedelta(hours=10, minutes=20),
            timedelta(hours=10, minutes=45),
        ],
    },
    (
        2, # Number of single Optimal
        0, # Number of couple Optimal
        3, # Number of single Ultimate
        0, # Number of couple Ultimate
        0, # Number of single Core
        0, # Number of couple Core
    ): {
        'Check-in, Consent & Change': [
            timedelta(hours=7, minutes=15),
            timedelta(hours=7, minutes=35),
            timedelta(hours=7, minutes=50),
            timedelta(hours=8, minutes=20),
            timedelta(hours=8, minutes=30),
        ],
    },
}

def format_hints_key(assessment: Assessment):
    return (assessment.data['num_single_clients'], assessment.data['num_couple_clients'])