"""Value Change Dump (VCD) file support.

.. autosummary::

    ~vcd.writer.VCDPhaseError
    ~vcd.writer.VCDWriter

"""
from .writer import VCDWriter, VCDPhaseError

__version__ = '0.0.1'

__all__ = ('VCDWriter', 'VCDPhaseError')
