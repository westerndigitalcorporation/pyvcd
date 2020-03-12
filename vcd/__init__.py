"""Value Change Dump (VCD) file support.

.. autosummary::

    ~vcd.writer.VCDPhaseError
    ~vcd.writer.VCDWriter

"""
from .writer import VCDPhaseError, VCDWriter

__all__ = ('VCDWriter', 'VCDPhaseError')
