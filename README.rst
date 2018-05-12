emonitor
========

Read and record data from serial instruments with python.

Tested using a Pfeiffer Maxigauge vacuum pressure gauge reader and a Lakeshore 336 temperature controller.

Install
-------

Install using setuptools.

.. code-block:: bash

   git clone https://github.com/ad3ller/emonitor
   cd ./emonitor
   python setup.py install
   pytest

Quick Start
-----------

`emonitor` can be started from a terminal with the command `run` and
the instrument name.

.. code-block:: bash

    $ emonitor run simulate --wait 10
    Starting emonitor. Use Ctrl-C to stop.

              TIMESTAMP            A	        B	        C
    2018-05-12 13:20:44	     292.7695	 293.5649	 293.9454
    2018-05-12 13:20:54	     292.9262	 293.5138	 293.9303
    2018-05-12 13:21:04	     293.0826	 293.3233	 294.0555
    2018-05-12 13:21:14	     293.1931	 293.4301	 294.0839
    ^C
    Stopping emonitor.


Configuration
-------------

Communication with a serial instrument is configured using `instrum.ini`.  To list configured instruments,

.. code-block:: bash

    $ emonitor ls
    ['simulate', 'maxigauge', 'lakeshore336']

To view the settings for a particular instrument,

.. code-block:: bash

    $ emonitor config lakeshore336
    [lakeshore336]
    db = temperature
    sensors = A, B, C
    cmd = KRDG?<sensor>\r\n
    parity = O
    stopbits = 1
    bytesize = 7
    baudrate = 57600
    port = COM8
    timeout = 1

And to modify a serial setting,

.. code-block:: bash

    $ emonitor set lakeshore336 --key "port" --value "COM7"

To configure a new instrument you will need to know the hardware serial settings and the `cmd` that `emonitor` can use to query the instrument.

Output
------

To store the sensor readings, simply redirect the output to a file (comma delimited).

.. code-block:: bash

    $ emonitor run simulate --wait 10 > "measurement.dat"

Or you can send them to an SQLite database.  This is a better option when running `emonitor` for long periods of time but it requires some extra setup.

Each instrument can be associated with its own SQLite database.  Set the database names in `instrum.ini`.

.. code-block:: bash

    $ emonitor set simulate --key db --value simulate_2018

Then initialise a database with a table that has columns that match the instrument sensor names,

.. code-block:: bash

    $ emonitor generate simulate

Enable SQLite output when running `emonitor` using the `--output` flag.

See the notebooks for examples for how to query an SQLite database.
