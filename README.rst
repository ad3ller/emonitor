emonitor
========

Read, record and plot sensor data from serial devices.

This application can be configured to work with generic serial devices.  It includes example configuration for a Pfeiffer MaxiGauge vacuum pressure gauge reader and a Lakeshore Model-336 temperature controller.

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

The `emonitor` commands can be executed from a terminal (or Anaconda prompt).

Configure the sensors for a (fake) serial device called `fake`.

.. code-block:: bash

    $ emonitor set fake --key sensors --value A B C

Next, create an SQLite database to store the fake data.

.. code-block:: bash

    $ emonitor generate fake
    Creating fake.db with columns ('A', 'B', 'C')

And finally, start the service.

.. code-block:: bash

    $ emonitor run fake --output --wait 10
    Starting emonitor. Use Ctrl-C to stop.

              TIMESTAMP            A	        B	        C
    2018-05-12 13:20:44	     292.7695	 293.5649	 293.9454
    2018-05-12 13:20:54	     292.9262	 293.5138	 293.9303
    2018-05-12 13:21:04	     293.0826	 293.3233	 294.0555
    2018-05-12 13:21:14	     293.1931	 293.4301	 294.0839


This queries the device for its sensor readings. Waits. And repeats.

To plot the recorded data in a browser using `bokeh <https://github.com/bokeh/bokeh>`_, launch another terminal and execute:

.. code-block:: bash

    $ emonitor plot --show


.. image:: docs/source/images/app.png
   :width: 300

Documentation
-------------

A guide to using ``emonitor`` is hosted on `emonitor.readthedocs.io <https://emonitor.readthedocs.io>`_.


Change log
----------

- v0.3.0, UTC timestamps (data taken before v0.3.0 should be adjusted to UTC for accurate plotting).