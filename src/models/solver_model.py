from enum import Enum
from dataclasses import dataclass, field
from typing import List
from datetime import timedelta

class ClientType(Enum):
    ELITE = 'ELITE'
    ULTIMATE = 'ULTIMATE'

class ConditionScope(Enum):
    ACTIVITY = 'ACTIVITY'
    ROOM = 'ROOM'

class ActivityConditionOption(Enum):
    BEFORE = 'BEFORE'
    AFTER = 'AFTER'
    RIGHT_AFTER = 'RIGHT_AFTER'
    RIGHT_BEFORE = 'RIGHT_BEFORE'
    BETWEEN = 'BETWEEN'
    WITHIN_AFTER = 'WITHIN_AFTER'
    WITHIN_BEFORE = 'WITHIN_BEFORE'
    IN_FIXED_ORDER_AS = 'IN_FIXED_ORDER_AS'

class ActivityConditionOptionType(Enum):
    ACTIVITY = 'ACTIVITY'
    TIME = 'TIME'
    ORDER = 'ORDER'
  
class RoomConditionOption(Enum):
    MAXIMUM = 'MAXIMUM'
    SAME = 'SAME'
    UNIQUE = 'UNIQUE'

class RoomConditionOptionType(Enum):
    ACTIVITY = 'ACTIVITY'
    CLIENT = 'CLIENT'

class RoomType(Enum):
    CLIENT = 'CLIENT'
    OTHER = 'OTHER'

@dataclass
class Condition:
    scope: ConditionScope
    option: ActivityConditionOption | RoomConditionOption
    option_type: ActivityConditionOptionType | None
    args: dict

@dataclass
class Room:
    id: str
    name: str
    type: RoomType
    floor: int
    conditions: List[Condition]
    
@dataclass
class ActivityRoom:
    room: Room
    duration: int

@dataclass
class Activity:
    id: str
    name: str
    conditions: List[Condition]
    rooms: List[ActivityRoom]

@dataclass
class Assessment:
    id: str
    name: str
    activities: List[Activity]
    quantity: int

@dataclass
class Client:
    id: str
    assessment: Assessment

ENUMS = set((
    ClientType,
    ConditionScope,
    ActivityConditionOption,
    ActivityConditionOptionType,
    RoomConditionOption,
    RoomConditionOptionType,
))

MODELS = set((
    Condition,
    Room,
    ActivityRoom,
    Activity,
    Assessment,
    Client,
))