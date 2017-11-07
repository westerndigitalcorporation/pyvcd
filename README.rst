PyVCD
=====

The PyVCD package writes Value Change Dump (VCD) files as specified in
IEEE 1364-2005.

Read the `documentation <http://pyvcd.readthedocs.io/en/latest/>`_.

Visit `PyVCD on GitHub <https://github.com/SanDisk-Open-Source/pyvcd>`_.

.. image:: https://readthedocs.org/projects/pyvcd/badge/?version=latest
   :target: http://pyvcd.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/SanDisk-Open-Source/pyvcd.svg?branch=master
   :target: https://travis-ci.org/SanDisk-Open-Source/pyvcd

.. image:: https://coveralls.io/repos/github/SanDisk-Open-Source/pyvcd/badge.svg?branch=master
   :target: https://coveralls.io/github/SanDisk-Open-Source/pyvcd?branch=master

Quick Start
-----------

.. code::

   >>> import sys
   >>> from vcd import VCDWriter
   >>> with VCDWriter(sys.stdout, timescale='1 ns', date='today') as writer:
   ...     counter_var = writer.register_var('a.b.c', 'counter', 'integer', size=8)
   ...     for timestamp, value in enumerate(range(10, 20, 2)):
   ...         writer.change(counter_var, timestamp, value)
   $date today $end
   $timescale 1 ns $end
   $scope module a $end
   $scope module b $end
   $scope module c $end
   $var integer 8 0 counter $end
   $upscope $end
   $upscope $end
   $upscope $end
   $enddefinitions $end
   #0
   $dumpvars
   b1010 0
   $end
   #1
   b1100 0
   #2
   b1110 0
   #3
   b10000 0
   #4
   b10010 0
