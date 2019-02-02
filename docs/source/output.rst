Output
------

text file
+++++++++

The simplest way to store sensor readings is to redirect them to a file.

::

    $ emonitor run fake --wait 10 > "fake.dat"

.. TIP::

    Use ``--no_header`` if appending data to an existing file with ``>>``.

Text data can be read using, e.g., notepad, excel.  

To read the file using `pandas <https://pandas.pydata.org/>`_,

::

    >>> import os
    >>> import pandas as pd
    >>> fil = os.path.join("~/", "fake.dat")
    >>> tcol = "TIMESTAMP"
    >>> df = pd.read_csv(fil, parse_dates=[tcol]).set_index(tcol)
    >>> df.head()
                                A         B         C         D
    TIMESTAMP                                                  
    2019-01-01 22:19:43  293.2937  293.6519  293.9759  294.4213
    2019-01-01 22:19:48  292.8743  293.5636  293.8714  294.4905
    2019-01-01 22:19:53  293.1201  293.5686  294.1647  294.4085
    2019-01-01 22:19:58  292.9944  293.6096  294.0472  294.6245
    2019-01-01 22:20:03  293.0680  293.6496  294.0408  294.5890


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

Alternatively, create the database explicitly,

::

    $ emonitor create fake_2018 --columns A B C D E --overwrite
    Creating fake_2018.db with columns ['A', 'B', 'C', 'D', 'E']

The SQLite files are stored in `~/.emonitor/data`.

Enable SQLite output with ``emonitor run`` using the ``--output`` flag.

SQL
+++

Sensor readings can be transmitted by ``emonitor`` to an SQL server (facilitated by `pymysql <https://pymysql.readthedocs.io>`_ and 
tested with MySQL and MariaDB servers).

.. WARNING::
    
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

Use ``emonitor set`` to assign the `sql_host`, `sql_port`, `sql_db` and `sql_table` settings.  With the exception of
`sql_table`, these can probably go in the DEFAULT section of the `config file <configure.html#output-settings>`_.

Enable SQL output with the ``--sql`` flag.

::
   
   $ emonitor run fake --sql
   SQL username: adam
   Enter password:

.. WARNING::

    Do not store `sql_passwd` in the config file in plain text.  If necessary, use ``emonitor passwd``
    to save it with basic encryption.  However, be aware that anyone with access to `instrum.ini` and
    the generated `private.key`  file will be able to decrypt the password.