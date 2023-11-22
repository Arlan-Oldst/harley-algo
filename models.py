from enum import Enum
from dataclasses import dataclass
from typing import List
from datetime import timedelta

class ClientType(Enum):
    OPTIMAL = 0
    ULTIMATE = 1

class ConditionScope(Enum):
    ACTIVITY = 0
    ROOM = 1

class ActivityConditionOption(Enum):
    BEFORE = 0
    AFTER = 1
    RIGHT_AFTER = 2
    BETWEEN = 3
    WITHIN = 4
    IN_FIXED_ORDER_AS = 5

class ActivityConditionOptionType(Enum):
    ACTIVITY = 0
    TIME = 1
    ORDER = 2
  
class RoomConditionOption(Enum):
    MAXIMUM = 0
    SAME = 1
    UNIQUE = 2

class RoomConditionOptionType(Enum):
    ACTIVITY = 0
    CLIENT = 1

@dataclass
class Condition:
    scope: ConditionScope
    option: ActivityConditionOption | RoomConditionOption
    option_type: ActivityConditionOptionType | None
    mandatory: bool
    args: dict

@dataclass
class Room:
    id: int
    name: str
    floor: int
    conditions: List[Condition]
    
@dataclass
class ActivityRoom:
    room: Room
    duration: int

@dataclass
class Activity:
    id: int
    name: str
    conditions: List[Condition]
    rooms: List[ActivityRoom]

@dataclass
class Assessment:
    id: int
    name: str
    activities: List[Activity]
    quantity: int

@dataclass
class Client:
    id: int
    assessment: Assessment