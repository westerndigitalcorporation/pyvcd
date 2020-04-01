Changelog
=========

pyvcd-0.2.0 (2020-04-01)
------------------------
* Breaking changes:

  * Python 3.6 is minimum version; drop Python 2 support
  * Remove ident argument from VCDWriter.register_var()

* Deprecations:

  * Enums for scope, variable, and timescale types
  * Enums for GTKWave flags and colors

* Features:

  * Inline type annotations, checkable with Mypy
  * Use base-94 encoding for variable identifiers
  * Improved performance

* Repairs:

  * Repair default string variable value
  * Ensure compound vector value correctness

* Development environment changes:

  * Add top-level Makefile with targets for common commands
  * Format code using black
  * Format imports using isort
  * Check type annotations with Mypy
  * Use GitHub Actions for CI; drop Travis

pyvcd-0.1.7 (2020-01-24)
------------------------
* Repair event variable changes (#14)

pyvcd-0.1.6 (2019-12-26)
------------------------
* Repair mis-formatted variable identifiers in dumps
* Exclude event and string types from dump_off
* Avoid duplicate timestamps in VCD output
* Avoid duplicate values in VCD output
* Improve performance when registering many variables in a scope (#12)

pyvcd-0.1.5 (2019-12-04)
------------------------
* Improve runtime performance by using write() (#9)
* Update package classifies to note Python 3.8 support

pyvcd-0.1.4 (2018-12-18)
------------------------
* Add "string" variable type
* Repair deprecated import of ABC's from collections.abc

pyvcd-0.1.3 (2017-02-21)
------------------------
* Allow initial timestamp other than 0 (#2)
* Repair unit tests to work on Windows (#3)

pyvcd-0.1.2 (2016-08-09)
------------------------
* GTKWSave per-group color cycles

pyvcd-0.1.1 (2016-07-06)
------------------------
* Improve README.rst
* Update copyright owner
* Use setuptools_scm to manage package version

pyvcd-0.1.0 (2016-07-05)
------------------------
* Initial public release
