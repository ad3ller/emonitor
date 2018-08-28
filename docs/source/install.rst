Install
-------

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
Sub-commands can be used to configure serial instruments, databases, or to start instances of
``emonitor``.

::

    $ emonitor --help
    usage: emonitor [-h]
                    {list,ls,config,new,copy,cp,delete,rm,set,drop,show,describe,generate,create,destroy,passwd,run}
                    ...

    emonitor

    optional arguments:
    -h, --help            show this help message and exit

    commands:
    
        config
        ------
        list (ls)           list instruments
        config              display instrument configuration
        new                 add a new instrument
        copy (cp)           copy instrument
        delete (rm)         delete instrument
        set                 set an instrument attribute
        drop                drop an instrument attribute
        
        sqlite
        ------
        show                show sqlite databases
        describe            describe an sqlite database
        generate            automatically create sqlite databases for the
                            configured instruments
        create              create sqlite database
        destroy             destroy sqlite database
    
        sql
        ---
        passwd              store password for an SQL server
    
        emonitor
        --------
        run                 start emonitor
