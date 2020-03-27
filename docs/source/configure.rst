Configure
=========

Communication with a serial device is configured using 
`~/.emonitor/instrum.ini`.  This file is also used to configure 
the recording of sensor data.

The configuration file can be viewed using ``emonitor config``. ::

    $ emonitor config
    [DEFAULT]
    sql_host = 127.0.0.1
    sql_port = 3306
    sql_db = emonitor
    plot_height = 400
    plot_width = 600

    [fake]
    db = fake
    sensors = ['A', 'B', 'C']
    sql_table = fake
    y_axis_label = Kelvin

    [maxigauge]
    device_class = pfeiffer.MaxiGauge
    db = pressure
    port = COM7
    sensors = ['1', '2', '3', '6']
    y_axis_label = mbar
    y_axis_type = log

    [lakeshore336]
    device_class = lakeshore.Model_336
    db = temperature
    y_axis_label = Kelvin
    sensors = ['A', 'B', 'C']
    port = COM8

The settings in the `DEFAULT` section are shared by all of the devices. 
These can be assigned using ``emonitor set``.

::

    $ emonitor set --key sql_port --value 3306

Similarly, ``emonitor set [instrum]`` can be used to assign settings for specific devices.

::

    $ emonitor set lakeshore336 --key port --value COM8

Or to set multiple values,

::

    $ emonitor set lakeshore336 --key sensors --value A B C

Each serial device has a section in the config file.  New sections can be added using the sub-commands ``new`` 
or ``copy`` (see ``--help`` for options).

serial settings
---------------

Classes for communicating with specific devices are accessible via the `device_class` setting.  E.g.,

:device_class:

    generic.Generic

    pfeiffer.MaxiGauge

    lakeshore.Model_336

    lakeshore.Model_331

These subclasses of ``serial.Serial`` have preconfigured settings and custom
methods. To read sensor data, ``emonitor`` attempts to call 
``emonitor/devices/[device_class](**settings).read_data(sensors)``.

It should be possible to configure ``emonitor`` to communicate with most serial devices using 
`device_class=generic.Generic` and the settings listed below. Examples configurations are 
available in `emonitor/examples/generic.ini`.

==================  =====================================================  
key                 description   
==================  =====================================================
port                device name, e.g., COM1
baudrate            data rate
bytesize            number of data bits
stopbits            number of stop bits
parity              enable parity checking
timeout             read timeout value
xonxoff             enable software flow control
rtsct               enable hardware (RTS/CTS) flow control
dsrdtr              enable hardware (DSR/DTR) flow control
write_timeout       write timeout value
inter_byte_timeout  inter-character timeout

cmd                 query instrument command with `{sensor}` placeholder
enq                 request data transmission
ack                 positive report signal
sensors             comma-delimited list of sensor names
regex               regular expression to format instrument response
==================  =====================================================

.. TIP::
   
   Serial communication is facilitated by `pyserial <https://pythonhosted.org/pyserial/>`_.  Test the settings and commands
   for communicating with a serial device using `serial.Serial() <https://pyserial.readthedocs.io/en/latest/pyserial_api.html>`_.   

output settings
---------------

The items below are used to configure emonitor's output. See `here <output.html>`_ for further details.

==========  ===============================================
key         description   
==========  ===============================================
db          name of SQLite database
tcol        name of timestamp column (default: "TIMESTAMP")
column_fmt  format column names, e.g., PG\_{sensor}
sql_host    SQL server ip address
sql_port    SQL server port number
sql_user    username with INSERT privileges
sql_passwd  password (encrypted)
sql_db      name of SQL database
sql_table   name of SQL table
==========  ===============================================

plot settings
--------------

The bokeh server also uses `~/.emonitor/instrum.ini` to customize its plots. 
Currently, only sqlite data can be plotted. As above, each of these settings
can be either DEFAULT or device-specific.

=============  ===============================================
key            description   
=============  ===============================================
plot_height      bokeh plot height [px]
plot_width      bokeh plot width [px]
plot_timezone    bokeh plot x-axis timezone.
                 E.g., 'Europe/Berlin'. See pytz.all_timezones
y_axis_label     bokeh plot y label
y_axis_type      bokeh plot y-axis type, e.g., "linear" or "log"
=============  ===============================================
