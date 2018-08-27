Output
------

Text file
+++++++++

The simplest way to store sensor readings is to redirect emonitor's output to a file (comma delimited).

::

    $ emonitor run fake --wait 10 > "fake.dat"

SQLite
++++++

Or you can send them to an SQLite database.  This is a much better option, especially when running ``emonitor`` for long periods
of time but it requires some extra setup.

Each instrument can be associated with its own SQLite database.  Set the database name for each instrument, e.g.,

::

    $ emonitor set fake --key db --value fake_2018

The sub-command ``generate`` creates an SQLite database and table for a given instrument, with columns that match the sensor names.

::

    $ emonitor generate fake
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D']

Enable SQLite output when running ``emonitor`` using the ``--output`` flag.
