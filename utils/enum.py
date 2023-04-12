from enum import auto, Enum


class eMigrationStatus(str, Enum):
    queued = auto()
    running = auto()
    done = auto()
    failed = auto()
    cancelled = auto()


class eRunningMethod(str, Enum):
    at_upgrade = auto()
    cron_job = auto()
