# mission_types.py
from enum import Enum, auto

class UnitMission(Enum):
    IDLE = auto()
    MOVE = auto()
    ATTACK = auto()
    HARVEST = auto()
    GUARD = auto()
    COLLECT_DROP = auto()
    MOVE_TO = auto()
    MINE = auto()
    BUILD = auto()