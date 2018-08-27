Configure
=========

instrum.ini
-----------

Communication with a serial instrument is configured using ``~/.emonitor/instrum.ini``.  This file is also used
to configure the recording of instrument readings.

The configuration file can be viewed using the ``emonitor`` sub-command, ``config``. ::

    $ emonitor config
    [DEFAULT]
    sql_host = 127.0.0.1
    sql_port = 3306
    sql_db = emonitor

    [fake]
    db = fake_2018
    sensors = A, B, C
    sql_table = fake
    port = COM7

    [maxigauge]
    db = pressure
    cmd = PR<sensor><CR><LF>
    ack = <ACK><CR><LF>
    enq = <ENQ>
    port = COM7
    baudrate = 9600
    stopbits = 1
    bytesize = 8
    parity = N
    timeout = 1
    regex = ,(.*)
    sensors = 1, 2, 3, 6
    column_fmt = <sensor>

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

The settings in the `DEFAULT` section are shared by all of the instruments.  These can be assigned using the ``set`` sub-command.

::

    $ emonitor set --key sql_port --value 3306

The ``set`` sub-command can also be used to assign settings for specific instruments.

::

    $ emonitor set lakeshore336 --key port --value COM8

Each serial instrument has a section in the config file.  New sections can be added using the sub-commands ``new`` 
or ``copy`` (see ``--help`` for options).

serial settings
---------------

It should be possible to configure `emonitor` to communicate with almost any serial instrument.  

Communication is fascilitated by the pyserial_ package.  Many of the settings listed below are 
used to initialise an instance of the class serial.Serial_.  Most settings are not mandetory.

.. _pyserial: https://pythonhosted.org/pyserial/
.. _serial.Serial: https://pyserial.readthedocs.io/en/latest/pyserial_api.html

==================  ==================================================   
name                description   
==================  ==================================================
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

cmd                 query instrument command with <sensor> placeholder
enq                 request data transmission             
ack                 positive report signal
sensors             comma-delimited list of sensor names
regex               regular expression to format instrument response
==================  ==================================================

output settings
---------------

See `Output <output.html>`_ for further details.

==========  =======================================
name        description   
==========  =======================================
db          name of SQLite database
column_fmt  format column names, e.g., PG\_<sensor>
sql_host    SQL server ip address
sql_port    SQL server port number
sql_user    username with INSERT priviledges
sql_passwd  password (encrypted)
sql_db      name of SQL database
sql_table   name of SQL table
==========  =======================================