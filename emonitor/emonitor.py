# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import glob
import time
import configparser
import argparse
import getpass
import sqlite3
import pymysql
from cryptography.fernet import Fernet
from humanize import naturalsize
from .core import TABLE, DATA_DIRE, INSTRUM_FILE, KEY_FILE, FakeSerialInstrument, SerialInstrument
from .tools import db_init, db_check, db_insert, db_count, db_describe

# config

def overwrite(config):
    """ save instrum.ini """
    with open(INSTRUM_FILE, 'w+', encoding='utf8') as fil:
        config.write(fil)

def list_instruments(args, config):
    """ list sections in the config file """
    print(config.sections())

def new_instrument(args, config):
    """ create a new configuration section """
    if config.has_section(args.output):
        if input("%s already exists. Overwrite (y/n) ?"%(args.output)).lower() in ['y', 'yes']:
            config.remove_section(args.output)
        else:
            sys.exit()
    config.add_section(args.output)
    overwrite(config)

def copy_instrument(args, config):
    """ copy config sections args.instrum to args.output (including any defaults)"""
    if not config.has_section(args.instrum):
        raise NameError("%s was not found in the config file"%(args.instrum))
    elif config.has_section(args.output):
        if args.force or input("%s already exists. Overwrite (y/n):"%(args.output)).lower() in ['y', 'yes']:
            config.remove_section(args.output)
        else:
            # abort
            sys.exit()
    config.add_section(args.output)
    for key, value in config.items(args.instrum):
        config.set(args.output, key, value)
    overwrite(config)

def delete_instrument(args, config):
    """ delete a section of the config file """
    if not config.has_section(args.instrum):
        if args.instrum == 'DEFAULT':
            raise Exception("Cannot remove DEFAULT section from instrum.ini")
        else:
            raise NameError("%s was not found in the config file"%(args.instrum))
    elif args.force or input("Are you sure you want to delete %s (y/n) ?"%(args.instrum)).lower() in ['y', 'yes']:
        # delete file
        config.remove_section(args.instrum)
        overwrite(config)
    else:
        # abort
        sys.exit()

def set_instrument_attribute(args, config):
    """ set an instrument attribute """
    if args.key == "sql_passwd":
        raise ValueError("Use passwd tool to store passwords.")
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        config.set(args.instrum, args.key, args.value)
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show_config(args, config)
    overwrite(config)

def drop_instrument_attribute(args, config):
    """ drop an instrument attribute """
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        if config.has_option(args.instrum, args.key):
            config.remove_option(args.instrum, args.key)
        else:
            raise NameError("%s.%s was not found in the config file"%(args.instrum, args.key))
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show_config(args, config)
    overwrite(config)

def show_config(args, config):
    """ print instrument configuration """
    if args.instrum == '__all__':
        config.write(sys.stdout)
    else:
        print('[%s]'%(args.instrum))
        for key, value in config.items(args.instrum):
            print('%s = %s'%(key, value))

# sqlite

def show_db_tables(args, config):
    '''  list sqlite database tables.
    '''
    fils = glob.glob(os.path.join(DATA_DIRE, '*.db'))
    if len(fils) == 0:
        print("No sqlite databases found.")
    else:
        fnames = [os.path.split(f)[1][:-3] for f in fils]
        print(fnames)

def describe_db(args, config):
    '''  describe sqlite database.
    '''
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if not os.path.isfile(fil):
        raise Exception("%s not found."%(fil))
    else:
        # info
        db = sqlite3.connect(fil)
        num_rows = db_count(db, TABLE)
        info = db_describe(db, TABLE)
        db.close()
        cols = [row[1] for row in info]
        # output
        print("path:", fil)
        print("size:", naturalsize(os.path.getsize(fil)))
        print("columns:", cols)
        print("rows:", "%d"%(num_rows))
        # schema
        if args.schema:
            print("schema:", "\n")
            for row in info:
                print(row)

def generate_db(args, config):
    ''' automatically create sqlite databases for configured instruments
    '''
    if len(args.instrums) == 0:
        args.instrums = config.sections()
    # check instrum exists
    for instrum in args.instrums:
        if not config.has_section(instrum):
            raise NameError("%s was not found in the config file"%(instrum))
        settings = dict(config.items(instrum))
        # database name
        if 'db' not in settings:
            raise NameError("'db' not configured for %s"%(instrum))
        db_name = settings['db']
        # get columns from instrument sensors
        if 'sensors' not in settings:
            raise NameError("'sensors' not configured for %s"%(instrum))
        if 'column_fmt' in settings:
            column_fmt = settings['column_fmt']
            columns = ('TIMESTAMP',) + tuple([column_fmt.replace('<sensor>', sen.strip()) for sen in settings['sensors'].split(',')])
        else:
            columns = ('TIMESTAMP',) + tuple([sen.strip() for sen in settings['sensors'].split(',')])
        # sqlite database
        fil = os.path.join(DATA_DIRE, db_name + '.db')
        ## check existing
        if os.path.exists(fil) and args.overwrite:
            if args.force or input("Are you sure you want to permanently destroy existing %s (y/n) ?"%(fil)).lower() in ['y', 'yes']:
                os.remove(fil)
        ## create
        if not os.path.exists(fil):
            if not args.quiet:
                print("Creating %s.db with columns"%(db_name), columns)
            db = sqlite3.connect(fil)
            db_init(db, TABLE, columns)
            db.close()

def create_db(args, config):
    '''  create sqlite database.
    '''
    if not isinstance(args.columns, list):
        raise TypeError("Columns must be a list")
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if os.path.isfile(fil):
        if args.force:
            os.remove(fil)
        else:
            raise Exception("Database already exists.  Use --force to overwrite.")
    db = sqlite3.connect(fil)
    db_init(db, TABLE, args.columns)
    db.close()

def destroy_db(args, config):
    '''  delete sqlite database.
    '''
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if os.path.isfile(fil):
        if args.force or input("Are you sure you want to permanently destroy %s (y/n) ?"%(fil)).lower() in ['y', 'yes']:
            os.remove(fil)
    else:
        raise Exception("Failed to destory. Database not found.")

# SQL server

def passwd(args, config):
    """ store SQL password.  
    """
    if args.instrum != 'DEFAULT' and not config.has_section(args.instrum):
        raise NameError("%s was not found in the config file"%(args.instrum))
    key = None
    if os.path.isfile(KEY_FILE):
        with open(KEY_FILE, "rb") as fil:
            key = fil.readline()
    if key is None or key == b'':
        # generate key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as fil:
            fil.write(key)
        os.chmod(KEY_FILE, 0o600)
    f = Fernet(key)
    prompt = f"enter password for {args.instrum}:"
    sql_passwd = bytes(getpass.getpass(prompt=prompt, stream=sys.stderr), 'utf-8')
    sql_passwd = f.encrypt(sql_passwd).decode('utf8')
    config.set(args.instrum, "sql_passwd", sql_passwd)
    overwrite(config)

# emonitor

def run(args, config):
    """ start the emonitor server and output to sqlite database.
    """
    tty = sys.stdout.isatty()
    close = not args.keep_open
    header = not args.no_header
    settings = dict(config.items(args.instrum))
    if 'column_fmt' in settings:
        column_fmt = settings['column_fmt']
        columns = ('TIMESTAMP',) + tuple([column_fmt.replace('<sensor>', sen.strip()) for sen in settings['sensors'].split(',')])
    else:
        columns = ('TIMESTAMP',) + tuple([sen.strip() for sen in settings['sensors'].split(',')])
    db = None
    sql_conn = None
    debug = False
    if debug and tty:
        print("DEBUG enabled")
    try:
        # serial connection
        if args.instrum in ['simulate', 'fake']:
            instrum = FakeSerialInstrument(settings)
        else:
            instrum = SerialInstrument(settings)
        # check output
        if args.output:
            if 'db' not in settings:
                raise Exception('db not specified in settings.')
            else:
                fil = os.path.join(DATA_DIRE, settings['db'] + '.db')
                if not os.path.isfile(fil):
                    raise Exception("Database %s does not exists.  Use generate or create."%(settings['db'] + '.db'))
                db = sqlite3.connect(fil)
                db_check(db, TABLE, columns)
        if args.sql:
            ## get sql database username and password
            assert 'sql_host' in settings, "sql_host not specified."
            assert 'sql_port' in settings, "sql_port not specified."
            assert 'sql_db' in settings, "sql_db not specified."
            assert 'sql_table' in settings, "sql_table not specified."
            if 'sql_user' not in settings:
                settings['sql_user'] = input('SQL user:')
            if 'sql_passwd' not in settings:
                prompt = f"{settings['sql_user']}@{settings['sql_host']} enter password:"
                sql_passwd = getpass.getpass(prompt=prompt, stream=sys.stderr)
            else:
                # decrypt password
                assert os.path.isfile(KEY_FILE), f"{KEY_FILE} not found.  Create using passwd."
                with open(KEY_FILE, "rb") as fil:
                    key = fil.readline()
                f = Fernet(key)
                sql_passwd = f.decrypt(bytes(settings['sql_passwd'], 'utf8')).decode('utf8')
            # connect
            sql_conn = pymysql.connect(host=settings['sql_host'],
                                       port=int(settings['sql_port']),
                                       user=settings['sql_user'],
                                       password=sql_passwd,
                                       database=settings['sql_db'])
        # header
        if tty:
            if not args.quiet:
                print("Starting emonitor. Use Ctrl-C to stop. \n")
                if header:
                    test = instrum.read_all(debug=debug, close=close)
                    str_width = len(str(test[0]))
                    print(columns[0].rjust(19) + ' \t', '\t '.join([col.rjust(str_width) for col in columns[1:]]))
        elif header:
            print(', '.join(columns))
        # start server
        while True:
            ## read data
            values = instrum.read_all(debug=debug, close=close)
            ## output data
            if isinstance(values, tuple):
                values = (time.strftime('%Y-%m-%d %H:%M:%S'), ) + values
                if tty:
                    if not args.quiet:
                        print('\t '.join(values))
                else:
                    print(', '.join(values))
                if args.output:                               
                    # send data
                    db_insert(db, TABLE, columns, values, debug=debug)
                if args.sql:
                    # sql data
                    db_insert(sql_conn, settings['sql_table'], columns, values, debug=debug)
            ## reset
            time.sleep(args.wait)
    except KeyboardInterrupt:
        # stop server
        if tty:
            if not args.quiet:
                print('\nStopping emonitor.')
    except:
        # catch all other exceptions
        raise
    finally:
        # clean up
        instrum.close()
        if db is not None:
            db.close()
        if sql_conn is not None:
            sql_conn.close()

DESCRIPTION = """
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
    """

def main():
    """ run emonitor as a script """
    # inputs
    #parser = argparse.ArgumentParser(description='emonitor server')
    parser = argparse.ArgumentParser(description='emonitor', formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(title='commands', dest='cmd', description=DESCRIPTION)
    subparsers.required = True

    # list instruments
    parser_ls = subparsers.add_parser('list', aliases=['ls'])
    parser_ls.set_defaults(func=list_instruments)

    # show config
    parser_show = subparsers.add_parser('config')
    parser_show.set_defaults(func=show_config)
    parser_show.add_argument('instrum', type=str, nargs='?', default="__all__",
                             help='serial intrument name [if None then all]')

    # new instrument
    parser_new = subparsers.add_parser('new')
    parser_new.set_defaults(func=new_instrument)
    parser_new.add_argument('output', type=str, help='new intrument name')

    # copy instrument
    parser_copy = subparsers.add_parser('copy', aliases=['cp'])
    parser_copy.set_defaults(func=copy_instrument)
    parser_copy.add_argument('instrum', type=str, help='existing intrument name')
    parser_copy.add_argument('output', type=str, help='new intrument name')
    parser_copy.add_argument('--force', action="store_true", default=False,
                             help="ignore warnings")

    # remove instrument
    parser_delete = subparsers.add_parser('delete', aliases=['rm'])
    parser_delete.set_defaults(func=delete_instrument)
    parser_delete.add_argument('instrum', type=str, help='intrument name')
    parser_delete.add_argument('--force', action="store_true", default=False,
                               help="ignore warnings")

    # set attrib
    parser_set = subparsers.add_parser('set')
    parser_set.set_defaults(func=set_instrument_attribute)
    parser_set.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                            help='intrument name [if None then DEFAULT]')
    parser_set.add_argument('-k', '--key', default=None,
                            help='attribute key, e.g., "port"')
    parser_set.add_argument('-v', '--value', default=None,
                            help='attribute value, e.g., "COM7"')
    parser_set.add_argument('-p', '--print', action="store_true", default=False,
                            help="print instrument configuration")

    # remove attrib
    parser_drop = subparsers.add_parser('drop')
    parser_drop.set_defaults(func=drop_instrument_attribute)
    parser_drop.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                             help='intrument name [if None then DEFAULT]')
    parser_drop.add_argument('key', default=None,
                             help='attribute key, e.g., "port"')
    parser_drop.add_argument('-p', '--print', action="store_true", default=False,
                             help="print instrument configuration")

    # list sqlite database tables
    parser_show = subparsers.add_parser('show')
    parser_show.set_defaults(func=show_db_tables)

    # describe sqlite3 database
    parser_describe = subparsers.add_parser('describe')
    parser_describe.set_defaults(func=describe_db)
    parser_describe.add_argument('db', type=str, help='database name')
    parser_describe.add_argument('-s', '--schema', action="store_true", default=False,
                               help="table structure")
 
     # auto-create sqlite3 database
    parser_generate = subparsers.add_parser('generate')
    parser_generate.set_defaults(func=generate_db)
    parser_generate.add_argument('instrums', nargs='*', help='instrument name(s) [if None then all].')
    parser_generate.add_argument('-q', '--quiet', action="store_true", default=False,
                            help="no printed output")
    parser_generate.add_argument('--overwrite', action="store_true", default=False,
                                 help="overwrite existing")
    parser_generate.add_argument('--force', action="store_true", default=False, help="ignore warnings")

    # create sqlite3 database
    parser_create = subparsers.add_parser('create')
    parser_create.set_defaults(func=create_db)
    parser_create.add_argument('db', type=str, help='database name')
    parser_create.add_argument('columns', nargs='+', help="table column(s)")
    parser_create.add_argument('--force', action="store_true", default=False, help="ignore warnings")

    # destroy sqlite3 database
    parser_destroy = subparsers.add_parser('destroy')
    parser_destroy.set_defaults(func=destroy_db)
    parser_destroy.add_argument('db', type=str, help='database name')
    parser_destroy.add_argument('--force', action="store_true", default=False, help="ignore warnings")

    # SQL database password
    parser_passwd = subparsers.add_parser('passwd')
    parser_passwd.set_defaults(func=passwd)
    parser_passwd.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                               help='intrument name [if None then DEFAULT]')

    # run server
    parser_run = subparsers.add_parser('run')
    parser_run.set_defaults(func=run)
    parser_run.add_argument('instrum', type=str, help='serial intrument name')
    parser_run.add_argument('-o', '--output', action="store_true", default=False,
                            help='enable SQLite output')
    parser_run.add_argument('-s', '--sql', action="store_true", default=False,
                            help='enable output to SQL server output')
    parser_run.add_argument('-w', '--wait', type=float, default=15.0,
                            help='wait time (s) between queries')
    parser_run.add_argument('-k', '--keep_open', action="store_true", default=False,
                            help="keep serial connection open between reads")
    parser_run.add_argument('-n', '--no_header', action="store_true", default=False,
                            help="don't print header, e.g., when appending to a file")
    # TODO probably PyQtGraph, maybe vispy
    #parser_run.add_argument('-p', '--plot', action="store_true", default=False,
    #                    help="live data plotting")
    parser_run.add_argument('-q', '--quiet', action="store_true", default=False,
                            help="no printed output")

    # read instrum.ini
    conf = configparser.ConfigParser()
    conf.read(INSTRUM_FILE)

    # execute
    user_args = parser.parse_args()
    user_args.func(user_args, conf)

if __name__ == "__main__":
    # execute only if run as a script
    main()
