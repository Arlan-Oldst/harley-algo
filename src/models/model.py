from enum import Enum
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import re

class ClientType(Enum):
    OPTIMAL = 'OPTIMAL'
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
    CARDIAC_ROOM = 'CARDIAC_ROOM'
    DOCTOR_ROOM = 'DOCTOR_ROOM'
    EYES_AND_EARS_ROOM = 'EYES_AND_EARS_ROOM'
    PHLEBOTOMY_ROOM = 'PHLEBOTOMY_ROOM'
    RADIOLOGY_ROOM = 'RADIOLOGY_ROOM'
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

class Record:
    def to_json(self) -> dict:
        return {
            re.sub(r'\_(.)', lambda k: k.group(1).upper(), key): attribute.to_json()
            if type(attribute) in MODELS
            else [
                subattribute.to_json()
                for subattribute in attribute
            ] if isinstance(attribute, list)
            else attribute.value
            if isinstance(attribute, Enum)
            else attribute.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            if isinstance(attribute, datetime)
            else attribute
            for key, attribute in self.__dict__.items()
        }

@dataclass
class Base(Record):
    created: datetime
    updated: datetime
    deleted: bool
    
@dataclass
class Resource(Base):
    resource_id: str
    resource_name: str
    type: ResourceTypes
    room_type: ResourceRoomTypes
    location: int
    available: bool = True
    data: dict = field(default_factory=dict)

@dataclass
class TimeAllocation(Record):
    male: int | None = None
    female: int | None = None
    default_time: int | None = None

@dataclass
class Activity(Base):
    activity_id: str
    room_type: str
    resource_type: ResourceTypes
    activity_name: str
    activity_color: str
    is_gender_time_allocated: bool = False
    enabled: bool = True
    time_allocations: TimeAllocation = field(default_factory=TimeAllocation)
    mandatory_conditions_count: int = 0
    optional_conditions_count: int = 0
    data: dict = field(default_factory=dict)

@dataclass
class BetweenValues(Record):
    start: str | None = None
    end: str | None = None

@dataclass
class Criteria(Record):
    criteria_type: CriteriaTypes
    between_values: BetweenValues
    value: str

@dataclass
class Condition(Base):
    condition_id: str
    activity_id: str
    assessment_id: str
    type: ConditionTypes
    enabled: bool = True
    generate: bool = False
    mandatory: bool = False
    criteria: Criteria = field(default_factory=Criteria)
    data: dict = field(default_factory=dict)

@dataclass
class GeneralCondition(Base):
    general_condition_id: str
    general_condition_title: str
    enabled: bool = True
    mandatory: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class Assessment(Base):
    assessment_id: str
    assessment_name: str
    enabled: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class AssessmentActivity(Base):
    assessment_activity_id: str
    assessment_id: str
    activity_id: str
    enabled: bool = False
    data: dict = field(default_factory=dict)

@dataclass
class ClientElite(Record):
    single_male: int = 0
    single_female: int = 0
    couple_male_female: int = 0
    couple_male_male: int = 0
    couple_female_female: int = 0

@dataclass
class ClientUltimate(Record):
    single_male: int = 0
    single_female: int = 0
    couple_male_female: int = 0
    couple_male_male: int = 0
    couple_female_female: int = 0

@dataclass
class ScenarioActionData(Record):
    out_order_rooms: List[str] = field(default_factory=list)
    client_elite: ClientElite = field(default_factory=ClientElite)
    client_ultimate: ClientUltimate = field(default_factory=ClientUltimate)

@dataclass
class ScenarioAction(Record):
    first_client_arrival_time: str
    max_gap: int = 10
    total_male: int | None = None
    total_female: int | None = None
    doctors_on_duty: int | None = None
    allow_simultaneous_transfers: bool = False
    data: ScenarioActionData = field(default_factory=ScenarioActionData)

@dataclass
class ScenarioActivity(Activity):
    conditions: List[Condition] = field(default_factory=list)
    movable: bool = False
    assigned_room: Resource = field(default_factory=Resource)
    assigned_time: int = 0

@dataclass
class TransferActivity(Record):
    activity_name: str
    time_allocations: TimeAllocation = field(default_factory=TimeAllocation)
    movable: bool | None = None
    assigned_time: int | None = None
    conditions: List[Condition] = field(default_factory=list)

@dataclass
class ClientScenario(Record):
    client_number: int
    client_type: ClientType
    type: ClientMaritalType
    sex: ClientSex
    single_client_no: int
    couple_client_no: int
    activities: List[ScenarioActivity | TransferActivity] = field(default_factory=list)
    client_room: Resource | None = None
    start_time: str | None = None

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
    ClientScenario,
    ScenarioActivity,
))