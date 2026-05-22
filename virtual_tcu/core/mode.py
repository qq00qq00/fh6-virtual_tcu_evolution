from enum import Enum

class Mode(Enum):
    COMFORT = "COMFORT"
    DYNAMIC = "DYNAMIC"
    RACE = "RACE"
    DRIFT = "DRIFT"
    OFFROAD = "OFFROAD"
    MANUAL = "MANUAL"


MODE_ORDER = [
    Mode.COMFORT,
    Mode.DYNAMIC,
    Mode.RACE,
    Mode.DRIFT,
    Mode.OFFROAD,
    Mode.MANUAL,
]
