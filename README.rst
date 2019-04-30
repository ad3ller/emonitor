emonitor
========

A command-line program for reading, recording and plotting sensor data from serial devices.

Designed to work with generic serial devices.  Includes example configuration for a Pfeiffer MaxiGauge vacuum pressure gauge reader and a Lakeshore Model-336 temperature controller.

Interactive plotting of live data is done with a `bokeh <https://github.com/bokeh/bokeh`_ server.

Install
-------

Requires python 3.6+. Tested using Anaconda on Windows 10 and Ubuntu 16.04.

Install using setuptools.

.. code-block:: bash

   git clone https://github.com/ad3ller/emonitor
   cd ./emonitor
   python setup.py install
   pytest

Quick Start
-----------

``emonitor`` can be started from a terminal (or Anaconda prompt) using the sub-command `run` and
the name of a configured serial device.

.. code-block:: bash

    $ emonitor set fake --key sensors --value A B C

    $ emonitor generate fake
    Creating fake.db with columns ('A', 'B', 'C')

    $ emonitor run fake -o --wait 10
    Starting emonitor. Use Ctrl-C to stop.

              TIMESTAMP            A	        B	        C
    2018-05-12 13:20:44	     292.7695	 293.5649	 293.9454
    2018-05-12 13:20:54	     292.9262	 293.5138	 293.9303
    2018-05-12 13:21:04	     293.0826	 293.3233	 294.0555
    2018-05-12 13:21:14	     293.1931	 293.4301	 294.0839


This queries the device for its sensor readings. Waits. And repeats.

The data is recorded to an SQLite database.  To plot the live data, launch another terminal and execute:

.. code-block:: bash

    $ emonitor plot --show


Documentation
-------------

A guide to using ``emonitor`` is hosted on `emonitor.readthedocs.io <https://emonitor.readthedocs.io>`_.
