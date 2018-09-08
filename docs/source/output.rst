Output
------

text file
+++++++++

The simplest way to store sensor readings is to redirect them to a file.

::

    $ emonitor run fake --wait 10 > "fake.dat"

.. TIP::

    Use ``--no_header`` if appending data to an existing file with ``>>``.

SQLite
++++++

Or you can send the data to an SQLite database.  This is a *much* better option!

Each device can be associated with its own database, e.g.,

::

    $ emonitor set fake --key db --value fake_2018

will set the name of the database for the device `fake` to `fake_2018.db`. 

``emonitor generate [instrum]`` automatically creates an SQLite database for a serial device, with a table called `data` and columns 
that match the device's sensors.

::

    $ emonitor generate fake
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D']

Alternatively, set the column names of the database explicitly,

::

    $ emonitor create fake_2018 A B C D E --overwrite
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D', 'E']

The SQLite files are stored in `~/.emonitor/data`.

Enable SQLite output with ``emonitor run`` using the ``--output`` flag.

SQL
+++

Sensor readings can be transmitted to an SQL server using `pymysql <https://pymysql.readthedocs.io>`_.  This 
might be appropriate for recording many GBs of data, or to make live sensor readings available over a network.

Assuming that you have a MySQL (or MariaDB or sim.) server installed and running, create a database and a user with INSERT privileges.
 
::

    mysql> CREATE DATABASE emonitor;

    mysql> CREATE USER '[username]'@'[IP address of emonitor machine]' IDENTIFIED BY '[password]';

    mysql> GRANT INSERT ON `emonitor`.* TO '[username]'@'[IP address of emonitor machine]';

    mysql> FLUSH PRIVILEGES;

.. NOTE::
   
   Similarly, grant SELECT privileges to any users that require remote access to the sensor data.

Now create tables for recording sensor data.  For example,

::

    mysql> USE emonitor;

    mysql> CREATE TABLE `temperature` (
    `TIMESTAMP` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `A` double DEFAULT NULL,
    `B` double DEFAULT NULL,
    `C` double DEFAULT NULL,
    `D` double DEFAULT NULL
    );

    mysql> quit;
    Bye

Use ``emonitor set`` to assign the `sql_*` settings listed `here <configure.html#output-settings>`_.

And enable SQL output with ``emonitor run [instrum] --sql``.

.. WARNING::

    There are many security risks associated with remote SQL servers.  
    Make regular backups, use strong and unique passwords, minimise privileges, and ensure
    that your server and firewall are configured correctly.