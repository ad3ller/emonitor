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

An SQLite database can be automatically created for a serial device.

::

    $ emonitor generate fake
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D']

The database contains a table called `data` with columns that match the device's sensors.

Alternatively, set the column names of the database explicitly,

::

    $ emonitor create fake_2018 A B C D E --overwrite
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D', 'E']

The SQLite files are stored in `~/.emonitor/data`.

Enable SQLite output with ``emonitor run`` using the ``--output`` flag.

SQL
+++

Sensor readings can be transmitted by ``emonitor`` to an SQL server (facilitated by `pymysql <https://pymysql.readthedocs.io>`_).
Tested with MySQL and MariaDB servers.

An SQL server is considerably more complicated to configure, maintain and secure than an SQLite database.
It is only recommended for very large databases or to make live sensor readings available over a network.

Connect to your SQL server and create a database and a user with INSERT privileges:

::

    mysql> CREATE DATABASE emonitor;

    mysql> CREATE USER '[username]'@'[IP address of emonitor machine]' IDENTIFIED BY '[password]';

    mysql> GRANT INSERT ON `emonitor`.* TO '[username]'@'[IP address of emonitor machine]';

    mysql> FLUSH PRIVILEGES;

.. NOTE::
   
   Also, grant SELECT privileges to any users that require remote access to the sensor data.

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