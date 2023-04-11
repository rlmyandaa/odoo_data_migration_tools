from enum import auto, Enum

class eMigrationStatus(str, Enum):
    queued = auto()
    running = auto()
    done = auto()
    failed = auto()
