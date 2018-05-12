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

              TIMESTAMP         A	        B	        C
    2018-05-12 13:20:44	 292.7695	 293.5649	 293.9454
    2018-05-12 13:20:54	 292.9262	 293.5138	 293.9303
    2018-05-12 13:21:04	 293.0826	 293.3233	 294.0555
    2018-05-12 13:21:14	 293.1931	 293.4301	 294.0839
    ^C
    Stopping emonitor.

To store the readings, simply redirect the output to a file (comma delimited).

.. code-block:: bash

    $ emonitor run simulate --wait 10 > "measurement.dat"

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

`emonitor` periodically transmits `cmd` to the instrument, swapping the placeholder '<sensor>' for each sensor name.
