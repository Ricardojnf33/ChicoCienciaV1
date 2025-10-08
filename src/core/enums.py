from enum import Enum, auto

class NodeType(Enum):
    HYPOTHESIS = auto()
    HYPERPARAM = auto()
    REPLICATION = auto()
    ABLATION = auto()
    AGGREGATE = auto()

class ExecStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    BUG = auto()
    NON_BUG = auto()

class Stage(Enum):
    PRELIM = 1
    TUNING = 2
    RESEARCH_GRADE = 3
    ABLATIONS = 4
