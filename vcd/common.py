from enum import Enum
from typing import NamedTuple


class ScopeType(Enum):
    """Valid VCD scope types."""

    begin = 'begin'
    fork = 'fork'
    function = 'function'
    module = 'module'
    task = 'task'


class VarType(Enum):
    """Valid VCD variable types."""

    event = 'event'
    integer = 'integer'
    parameter = 'parameter'
    real = 'real'
    realtime = 'realtime'
    reg = 'reg'
    supply0 = 'supply0'
    supply1 = 'supply1'
    time = 'time'
    tri = 'tri'
    triand = 'triand'
    trior = 'trior'
    trireg = 'trireg'
    tri0 = 'tri0'
    tri1 = 'tri1'
    wand = 'wand'
    wire = 'wire'
    wor = 'wor'
    string = 'string'

    def __str__(self) -> str:
        return self.value


class TimescaleMagnitude(Enum):
    """Valid timescale magnitudes."""

    one = 1
    ten = 10
    hundred = 100


class TimescaleUnit(Enum):
    """Valid timescale units."""

    second = 's'
    millisecond = 'ms'
    microsecond = 'us'
    nanosecond = 'ns'
    picosecond = 'ps'
    femtosecond = 'fs'


class Timescale(NamedTuple):
    """Timescale magnitude and unit."""

    magnitude: TimescaleMagnitude
    unit: TimescaleUnit
