"""Value Change Dump (VCD) file support.

.. autosummary::

    ~vcd.writer.VCDPhaseError
    ~vcd.writer.VCDWriter

"""
from .writer import VCDWriter, VCDPhaseError

__all__ = ('VCDWriter', 'VCDPhaseError')
