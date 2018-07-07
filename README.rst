emonitor
========

A simple command-line program for reading and recording data from serial instruments.

Requires python 3.6+. Tested using Anaconda on Windows 10 and Ubuntu 16.04.

Example configuration for a Pfeiffer Maxigauge vacuum pressure gauge reader and a Lakeshore 336 temperature controller.

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

`emonitor` can be started from a terminal (or Anaconda prompt) using the sub-command `run` and
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

The program queries the instrument for its sensor readings. Waits. And repeats.

Configuration
-------------

Communication with a serial instrument is configured using `~/.emonitor/instrum.ini`.  To list the configured instruments,

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

And to modify a setting,

.. code-block:: bash

    $ emonitor set lakeshore336 --key "port" --value "COM7"

To configure a new instrument you will need to know the serial settings and the `cmd` that `emonitor` can use to query the hardware. Responses can be formatted using `regex`.

Output
------

Text file
+++++++++

The simplest way to store sensor readings is to redirect emonitor's output to a file (comma delimited).

.. code-block:: bash

    $ emonitor run simulate --wait 10 > "measurement.dat"

SQLite
++++++

Or you can send them to an SQLite database.  This is a better option when running `emonitor` for long periods of time but it requires some extra setup.

Each instrument can be associated with its own SQLite database.  Set the database names in `instrum.ini`.

.. code-block:: bash

    $ emonitor set simulate --key db --value simulate_2018

The sub-command `generate` creates an SQLite database for a given instrument with a table called `data` which has columns that match the sensor names,

.. code-block:: bash

    $ emonitor generate simulate
    Creating simulate_2018.db with columns ['A', 'B', 'C', 'D']

Enable SQLite output when running `emonitor` using the `--output` flag.

See the notebooks for examples for how to plot readings from an SQLite database.
