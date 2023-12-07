from enum import Enum
from dataclasses import dataclass, field
from typing import List
from datetime import timedelta

class ClientType(Enum):
    ELITE = 'ELITE'
    ULTIMATE = 'ULTIMATE'

class ClientMaritalType(Enum):
    SINGLE = 'SINGLE'
    COUPLE = 'COUPLE'
    
class ClientSex(Enum):
    MALE = 'MALE'
    FEMALE = 'FEMALE'

class ResourceTypes(Enum):
    CLIENT = 'CLIENT'
    OTHER = 'OTHER'

class ResourceRoomTypes(Enum):
    # CLIENT
    SINGLE_CLIENT_ROOM = 'SINGLE_CLIENT_ROOM'
    DOUBLE_CLIENT_ROOM = 'DOUBLE_CLIENT_ROOM'
    DOUBLE_ACCESSIBLE = 'DOUBLE_ACCESSIBLE'
    
    # OTHER
    ULTRASOUND_ROOM = 'ULTRASOUND_ROOM'
    MRI_15T_ROOM = 'MRI_1.5T_ROOM'
    MRI_3T_ROOM = 'MRI_3T_ROOM'
    CARDIAC_ROOM = 'CARDIAC_ROOM',
    DOCTOR_ROOM = 'DOCTOR_ROOM',
    EYES_AND_EARS_ROOM = 'EYES_AND_EARS_ROOM',
    PHLEBOTOMY_ROOM = 'PHLEBOTOMY_ROOM',
    RADIOLOGY_ROOM = 'RADIOLOGY_ROOM',
    PURE_SPORTS_ROOM = 'PURE_SPORTS_ROOM'

class ResourceLocations(Enum):
    LOWER_LEVEL = 0
    UPPER_LEVEL = 1
    PURE_SPORTS = 2

class ConditionTypes(Enum):
    BEFORE = 'BEFORE'
    AFTER = 'AFTER'
    BETWEEN = 'BETWEEN'
    WITHIN = 'WITHIN'
    IN_FIXED_ORDER_AS = 'IN_FIXED_ORDER_AS'
    RIGHT_AFTER = 'RIGHT_AFTER'

class CriteriaTypes(Enum):
    ACTIVITY = 'ACTIVITY'
    TIME = 'TIME'
    ORDER = 'ORDER'

@dataclass
class Resource:
    resource_id: str
    resource_name: str
    type: ResourceTypes
    room_type: ResourceRoomTypes
    location: int
    available: bool = True
    deleted: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class TimeAllocation:
    male: int | None = None
    female: int | None = None
    default_time: int | None = None

@dataclass
class Activity:
    activity_id: str
    room_type: str
    resource_type: ResourceTypes
    activity_name: str
    activity_color: str
    is_gender_time_allocated: bool = False
    enabled: bool = True
    deleted: bool = False
    time_allocations: TimeAllocation = field(default_factory=TimeAllocation)
    mandatory_conditions_count: int = 0
    optional_conditions_count: int = 0
    data: dict = field(default_factory=dict)

@dataclass
class BetweenValues:
    start: str | None = None
    end: str | None = None

@dataclass
class Criteria:
    criteria_type: CriteriaTypes
    between_values: BetweenValues
    value: str

@dataclass
class Condition:
    condition_id: str
    condition_title: str
    activity_id: str
    assessment_id: str
    type: ConditionTypes
    enabled: bool = True
    generate: bool = False
    mandatory: bool = False
    deleted: bool = False
    criteria: Criteria = field(default_factory=Criteria)
    data: dict = field(default_factory=dict)

@dataclass
class GeneralCondition:
    general_condition_id: str
    general_condition_title: str
    enabled: bool = True
    mandatory: bool = False
    deleted: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class Assessment:
    assessment_id: str
    assessment_name: str
    assessment_color: str
    enabled: bool = False
    deleted: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class AssessmentActivity:
    assessment_activity_id: str
    assessment_id: str
    activity_id: str
    enabled: bool = False
    deleted: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class ClientElite:
    single_male: int = 0
    single_female: int = 0
    couple_male_female: int = 0
    couple_male_male: int = 0
    couple_female_female: int = 0

@dataclass
class ClientUltimate:
    single_male: int = 0
    single_female: int = 0
    couple_male_female: int = 0
    couple_male_male: int = 0
    couple_female_female: int = 0

@dataclass
class ScenarioActionData:
    out_order_rooms: List[str] = field(default_factory=list)
    client_elite: ClientElite = field(default_factory=ClientElite)
    client_ultimate: ClientUltimate = field(default_factory=ClientUltimate)

@dataclass
class ScenarioAction:
    scenario_action_id: str
    first_client_arrival_time: str
    max_gap: int = 10
    total_male: int | None = None
    total_female: int | None = None
    doctors_on_duty: int | None = None
    allow_simultaneous_transfers: bool = False
    data: ScenarioActionData = field(default_factory=ScenarioActionData)

@dataclass
class GeneratedScenarioData:
    client_number: int
    client_type: ClientType
    type: ClientMaritalType
    sex: ClientSex
    couple_index: int
    couple_client_number: int
    activities: List[Activity]

@dataclass
class GeneratedScenario:
    data: List[GeneratedScenarioData]

ENUMS = set((
    ClientType,
    ClientMaritalType,
    ClientSex,
    ResourceTypes,
    ResourceRoomTypes,
    ResourceLocations,
    ConditionTypes,
    CriteriaTypes,
))

MODELS = set((
    Resource,
    TimeAllocation,
    Activity,
    BetweenValues,
    Criteria,
    Condition,
    GeneralCondition,
    Assessment,
    AssessmentActivity,
    ClientElite,
    ClientUltimate,
    ScenarioActionData,
    ScenarioAction,
    GeneratedScenarioData,
    GeneratedScenario,
))