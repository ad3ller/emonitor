Quick Start
-----------

List the configured serial devices,

::

   $ emonitor ls
   ['fake', 'maxigauge', 'lakeshore336']


Set the serial port for `fake`,

::
   
   $ emonitor set fake --key port --value COM7

Then run ``emonitor`` for this device,

::

    $ emonitor run fake --wait 10
    Starting emonitor. Use Ctrl-C to stop.

              TIMESTAMP            A	        B	        C
    2018-05-12 13:20:44	     292.7695	 293.5649	 293.9454
    2018-05-12 13:20:54	     292.9262	 293.5138	 293.9303
    2018-05-12 13:21:04	     293.0826	 293.3233	 294.0555
    2018-05-12 13:21:14	     293.1931	 293.4301	 294.0839
    ^C
    Stopping emonitor.

This queries the device for its sensor readings. Waits. And repeats.