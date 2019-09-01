Install
-------

Requires python 3.6+.

Clone the latest version of ``emonitor`` from `github.com <https://github.com/ad3ller/emonitor>`_,

::

   $ git clone https://github.com/ad3ller/emonitor
   $ cd ./emonitor

Then install using `setuptools <https://setuptools.readthedocs.io/en/latest/>`_,

::

   $ python setup.py install

And run tests with `pytest <https://docs.pytest.org>`_,

::

   $ pytest

Once installed, ``emonitor`` can be accessed from a terminal (or Anaconda prompt).  
Sub-commands can be used to configure communication with serial devices and 
databases, or to run ``emonitor``.

::

    $ emonitor --help
    usage: emonitor [-h]
                    {list,ls,config,new,copy,cp,delete,rm,set,drop,show,describe,generate,create,destroy,passwd,run}
                    ...

    emonitor

    optional arguments:
        -h, --help            show this help message and exit

    command:

         config
         ------
         list (ls)           list devices
         config              display [device] configuration
         new                 add device
         copy (cp)           copy device configuration
         remove (rm)         remove device
         set                 set a device attribute
         drop                drop a device attribute

         data
         ----
         show                show SQLite databases
         describe            describe an SQLite database
         create              create SQLite database
         generate            automatically create SQLite databases
                             for the configured devices
         destroy             destroy SQLite database

         SQL
         ---
         passwd              store password for an SQL server

         emonitor
         --------
         run                 start emonitor

         plotting
         --------
         plot                start bokeh server