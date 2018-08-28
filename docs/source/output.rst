Output
------

text file
+++++++++

The simplest way to store sensor readings is to redirect emonitor's output to a file.

::

    $ emonitor run fake --wait 10 > "fake.dat"

.. TIP::

    Use ``--no_header`` if appending data to an existing file with ``>>``.

sqlite
++++++

Or you can send the data to an sqlite database.  This is a much better option but it requires some extra setup.

Each instrument can be associated with its own database.  Set the database name for each instrument, e.g.,

::

    $ emonitor set fake --key db --value fake_2018

The sub-command ``generate`` creates an sqlite database and table for a given instrument, with columns that match its sensor names.

::

    $ emonitor generate fake
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D']

Enable sqlite output with ``emonitor run`` using ``--output``.
