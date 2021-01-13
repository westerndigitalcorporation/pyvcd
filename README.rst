PyVCD
=====

The PyVCD package writes Value Change Dump (VCD) files as specified in
IEEE 1364-2005.

Read the `documentation <http://pyvcd.readthedocs.io/en/latest/>`_.

Visit `PyVCD on GitHub <https://github.com/westerndigitalcorporation/pyvcd>`_.

.. image:: https://readthedocs.org/projects/pyvcd/badge/?version=latest
   :target: http://pyvcd.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/westerndigitalcorporation/pyvcd/workflows/CI/badge.svg
   :target: https://github.com/westerndigitalcorporation/pyvcd/actions?query=workflow%3ACI

.. image:: https://coveralls.io/repos/github/westerndigitalcorporation/pyvcd/badge.svg?branch=master
   :target: https://coveralls.io/github/westerndigitalcorporation/pyvcd?branch=master

Quick Start
-----------

.. code::

   >>> import sys
   >>> from vcd import VCDWriter
   >>> with VCDWriter(sys.stdout, timescale='1 ns', date='today') as writer:
   ...     counter_var = writer.register_var('a.b.c', 'counter', 'integer', size=8)
   ...     real_var = writer.register_var('a.b.c', 'x', 'real', init=1.23)
   ...     for timestamp, value in enumerate(range(10, 20, 2)):
   ...         writer.change(counter_var, timestamp, value)
   ...     writer.change(real_var, 5, 3.21)
   $date today $end
   $timescale 1 ns $end
   $scope module a $end
   $scope module b $end
   $scope module c $end
   $var integer 8 ! counter $end
   $var real 64 " x $end
   $upscope $end
   $upscope $end
   $upscope $end
   $enddefinitions $end
   #0
   $dumpvars
   b1010 !
   r1.23 "
   $end
   #1
   b1100 !
   #2
   b1110 !
   #3
   b10000 !
   #4
   b10010 !
   #5
   r3.21 "
