===========================
Generating SQLite Results
===========================

.. note ::

   New in ???

.. autoplugin :: nose2.plugins.sqlite.SQLiteReporter

Database Schema
---------------

The database current has three tables runs, results, and props.  It is 
intended that this file be readable during operations, though this has
not be extensively tested.

runs
....

* id - a generated UUID used to mark associated tests.
* start - start timestamp for run.
* finish - ending timestamp for run.
  
results
.......

* id - auto-generated integer.
* name - test name from nose.
* runid - the UUID from the run table.
* desc - test.shortDescription()
* result - passed, failed, etc.
* msg - outcome message.
* start - start timestamp for run.
* finish - ending timestamp for run.

props
.....

* id - the test id from result.s
* key - a metadata value name.
* value - a corresponding string value.
