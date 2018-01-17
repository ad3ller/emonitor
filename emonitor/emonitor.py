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
import sqlite3
from .core import DATA_DIRE, INSTRUM_FILE, FakeInstrument, Instrument
from .sqlite_tools import initialize as db_init
from .sqlite_tools import check as db_check
from .sqlite_tools import insert as db_insert

# config

def overwrite(config):
    """ save instrum.ini """
    with open(INSTRUM_FILE, 'w+', encoding='utf8') as fil:
        config.write(fil)

def clist(args, config):
    """ list sections in the config file """
    print(config.sections())

def new(args, config):
    """ create a new configuration section """
    if config.has_section(args.output):
        if input("%s already exists. Overwrite (y/n):"%(args.output)).lower() in ['y', 'yes']:
            config.remove_section(args.output)
        else:
            sys.exit()
    config.add_section(args.output)
    overwrite(config)

def copy(args, config):
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

def delete(args, config):
    """ delete a section of the config file """
    if not config.has_section(args.instrum):
        if args.instrum == 'DEFAULT':
            raise Exception("Cannot remove DEFAULT section from instrum.ini")
        else:
            raise NameError("%s was not found in the config file"%(args.instrum))
    elif args.force or input("Are you sure you want to delete %s (y/n):"%(args.instrum)).lower() in ['y', 'yes']:
        # delete file
        config.remove_section(args.instrum)
        overwrite(config)
    else:
        # abort
        sys.exit()

def cset(args, config):
    """ set an instrument attribute """
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        config.set(args.instrum, args.key, args.value)
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show(args, config)
    overwrite(config)

def drop(args, config):
    """ drop an instrument attribute """
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        if config.has_option(args.instrum, args.key):
            config.remove_option(args.instrum, args.key)
        else:
            raise NameError("%s.%s was not found in the config file"%(args.instrum, args.key))
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show(args, config)
    overwrite(config)

def show(args, config):
    """ print instrument configuration """
    if args.instrum == '__all__':
        config.write(sys.stdout)
    else:
        print('[%s]'%(args.instrum))
        for key, value in config.items(args.instrum):
            print('%s = %s'%(key, value))

# sqlite

def create(args, config):
    '''  create sqlite database.
    '''
    if not isinstance(args.columns, list):
        raise TypeError("columns must be a list")
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if os.path.isfile(fil):
        if args.force:
            os.remove(fil)
        else:
            raise Exception("database already exists.  Use --force to overwrite.")
    db = sqlite3.connect(fil)
    db_init(db, 'data', args.columns)
    db.close()

def tables(args, config):
    '''  list sqlite database tables.
    '''
    fils = glob.glob(os.path.join(DATA_DIRE, '*.db'))
    if len(fils) == 0:
        print("no sqlite databases found.")
    else:
        fnames = [os.path.split(f)[1][:-3] for f in fils]
        print(fnames)

# emonitor

def run(args, config):
    """ start the emonitor server and output to sqlite database.
    """
    tty = sys.stdout.isatty()
    close = not args.keep_open
    settings = dict(config.items(args.instrum))
    columns = ('TIMESTAMP',) + tuple([sen.strip() for sen in settings['sensors'].split(',')])
    db = None
    debug = False
    try:
        # serial connection
        if args.instrum == 'simulate':
            instrum = FakeInstrument(settings)
        else:
            instrum = Instrument(settings)
        # check output
        if args.output:
            if 'db' not in settings:
                raise Exception('db not specified in settings.')
            else:
                fil = os.path.join(DATA_DIRE, settings['db'] + '.db')
                if not os.path.isfile(fil):
                    raise Exception("Database %s does not exists.  Use emonitor create."%(settings['db'] + '.db'))
                db = sqlite3.connect(fil)
                db_check(db, 'data', columns)
        # header
        if tty:
            if not args.quiet:
                print("Starting emonitor. Use Ctrl-C to stop. \n")
                test = instrum.read_all(debug=debug, close=close)
                str_width = len(str(test[0]))
                print(columns[0].rjust(19) + ' \t', '\t '.join([col.rjust(str_width) for col in columns[1:]]))
        else:
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
                    db_insert(db, 'data', columns, values, debug=debug)
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

def main():
    """ run emonitor as a script """
    # inputs
    parser = argparse.ArgumentParser(description='emonitor server')
    subparsers = parser.add_subparsers(title='commands', dest='cmd', help='cmd')
    subparsers.required = True

    # list instruments
    parser_ls = subparsers.add_parser('list', aliases=['ls'], help='list the configured instruments')
    parser_ls.set_defaults(func=clist)

    # new instrument
    parser_new = subparsers.add_parser('new', help='add a new instrument')
    parser_new.set_defaults(func=new)
    parser_new.add_argument('output', type=str, help='new intrument name')

    # copy instrument
    parser_copy = subparsers.add_parser('copy', aliases=['cp'],
                                        help='copy configuration to a new instrument')
    parser_copy.set_defaults(func=copy)
    parser_copy.add_argument('instrum', type=str, help='existing intrument name')
    parser_copy.add_argument('output', type=str, help='new intrument name')
    parser_copy.add_argument('-f', '--force', action="store_true", default=False,
                             help="ignore warnings")

    # remove instrument
    parser_delete = subparsers.add_parser('delete', help='delete instrument')
    parser_delete.set_defaults(func=delete)
    parser_delete.add_argument('instrum', type=str, help='intrument name')
    parser_delete.add_argument('-f', '--force', action="store_true", default=False,
                               help="ignore warnings")

    # show config
    parser_show = subparsers.add_parser('config', help='print instrument configuration')
    parser_show.set_defaults(func=show)
    parser_show.add_argument('instrum', type=str, nargs='?', default="__all__",
                             help='serial intrument name [if None then all]')

    # set attrib
    parser_set = subparsers.add_parser('set', help='set an instrument attribute')
    parser_set.set_defaults(func=cset)
    parser_set.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                            help='intrument name [if None then DEFAULT]')
    parser_set.add_argument('-k', '--key', default=None,
                            help='attribute key, e.g., "port"')
    parser_set.add_argument('-v', '--value', default=None,
                            help='attribute value, e.g., "COM7"')
    parser_set.add_argument('-p', '--print', action="store_true", default=False,
                            help="print instrument configuration")

    # remove attrib
    parser_drop = subparsers.add_parser('drop', help='drop an instrument attribute')
    parser_drop.set_defaults(func=drop)
    parser_drop.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                             help='intrument name [if None then DEFAULT]')
    parser_drop.add_argument('key', default=None,
                             help='attribute key, e.g., "port"')
    parser_drop.add_argument('-p', '--print', action="store_true", default=False,
                             help="print instrument configuration")

    # create sqlite3 database
    parser_create = subparsers.add_parser('create', help='create an sqlite database table')
    parser_create.set_defaults(func=create)
    parser_create.add_argument('db', type=str, help='database name')
    parser_create.add_argument('columns', nargs='+', help="table column(s)")
    parser_create.add_argument('-f', '--force', action="store_true", default=False,
                               help="ignore warnings")
    # list sqlite database tables
    parser_create = subparsers.add_parser('tables', help='list sqlite database tables')
    parser_create.set_defaults(func=tables)

    # run server
    parser_run = subparsers.add_parser('run', help='start the emonitor server')
    parser_run.set_defaults(func=run)
    parser_run.add_argument('instrum', type=str, help='serial intrument name')
    parser_run.add_argument('-o', '--output', action="store_true", default=False,
                            help='enable output')
    parser_run.add_argument('-w', '--wait', type=float, default=15.0,
                            help='wait time (s) between queries')
    parser_run.add_argument('-k', '--keep_open', action="store_true", default=False,
                            help="keep serial connection open between reads")
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
