# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import configparser
import argparse
from .core import INSTRUM_FILE
from .database import (show_db_tables,
                       describe_db,
                       generate_db,
                       create_db,
                       destroy_db)
from .config import (list_instruments,
                     new_instrument,
                     copy_instrument,
                     delete_instrument,
                     set_instrument_attribute,
                     drop_instrument_attribute,
                     show_config,
                     passwd)
from .run import run


DESCRIPTION = """
    config
    ------
    list (ls)           list devices
    config              display [device] configuration
    new                 add device
    copy (cp)           copy device configuration
    remove (rm)         remove device
    set                 set a device attribute
    drop                drop a device attribute

    SQLite
    ------
    show                show SQLite databases
    describe            describe an SQLite database
    generate            automatically create SQLite databases
                        for the configured devices
    create              create SQLite database
    destroy             destroy SQLite database

    SQL
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
                             help='serial device name [if None then all]')

    # new instrument
    parser_new = subparsers.add_parser('new')
    parser_new.set_defaults(func=new_instrument)
    parser_new.add_argument('output', type=str, help='new device name')

    # copy instrument
    parser_copy = subparsers.add_parser('copy', aliases=['cp'])
    parser_copy.set_defaults(func=copy_instrument)
    parser_copy.add_argument('instrum', type=str, help='existing device name')
    parser_copy.add_argument('output', type=str, help='new device name')
    parser_copy.add_argument('--force', action="store_true", default=False,
                             help="ignore warnings")

    # remove instrument
    parser_delete = subparsers.add_parser('remove', aliases=['rm'])
    parser_delete.set_defaults(func=delete_instrument)
    parser_delete.add_argument('instrum', type=str, help='device name')
    parser_delete.add_argument('--force', action="store_true", default=False,
                               help="ignore warnings")

    # set attrib
    parser_set = subparsers.add_parser('set')
    parser_set.set_defaults(func=set_instrument_attribute)
    parser_set.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                            help='device name [if None then DEFAULT]')
    parser_set.add_argument('-k', '--key', required=True,
                            help='attribute key, e.g., "port"')
    parser_set.add_argument('-v', '--value', nargs='+', required=True,
                            help='attribute value, e.g., "COM7"')
    parser_set.add_argument('-p', '--print', action="store_true", default=False,
                            help="display device configuration")

    # remove attrib
    parser_drop = subparsers.add_parser('drop')
    parser_drop.set_defaults(func=drop_instrument_attribute)
    parser_drop.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                             help='device name [if None then DEFAULT]')
    parser_drop.add_argument('-k', '--key', required=True,
                             help='attribute key, e.g., "port"')
    parser_drop.add_argument('-p', '--print', action="store_true", default=False,
                             help="display device configuration")

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
    parser_generate.add_argument('instrums', nargs='*', help='device name(s) [if None then all].')
    parser_generate.add_argument('-q', '--quiet', action="store_true", default=False,
                                 help="no printed output")
    parser_generate.add_argument('--overwrite', action="store_true", default=False,
                                 help="overwrite existing")
    parser_generate.add_argument('--force', action="store_true", default=False, help="ignore warnings")

    # create sqlite3 database
    parser_create = subparsers.add_parser('create')
    parser_create.set_defaults(func=create_db)
    parser_create.add_argument('db', type=str, help='database name')
    parser_create.add_argument('-c', '--columns', nargs='+', required=True, help="table column(s)")
    parser_create.add_argument('-q', '--quiet', action="store_true", default=False,
                               help="no printed output")
    parser_create.add_argument('--overwrite', action="store_true", default=False,
                               help="overwrite existing")

    # destroy sqlite3 database
    parser_destroy = subparsers.add_parser('destroy')
    parser_destroy.set_defaults(func=destroy_db)
    parser_destroy.add_argument('db', type=str, help='database name')
    parser_destroy.add_argument('--force', action="store_true", default=False, help="ignore warnings")

    # SQL database password
    parser_passwd = subparsers.add_parser('passwd')
    parser_passwd.set_defaults(func=passwd)
    parser_passwd.add_argument('instrum', type=str, nargs='?', default="DEFAULT",
                               help='device name [if None then DEFAULT]')

    # run server
    parser_run = subparsers.add_parser('run')
    parser_run.set_defaults(func=run)
    parser_run.add_argument('instrum', type=str, help='serial device name')
    parser_run.add_argument('--debug', action="store_true", default=False,
                            help='enable debugging info')
    parser_run.add_argument('-o', '--output', action="store_true", default=False,
                            help='enable SQLite output')
    parser_run.add_argument('-s', '--sql', action="store_true", default=False,
                            help='enable output to SQL server output')
    parser_run.add_argument('-w', '--wait', type=float, default=15.0,
                            help='wait time (s) between queries')
    parser_run.add_argument('-n', '--no_header', action="store_true", default=False,
                            help="don't print header, e.g., when appending to a file")
    # TODO probably PyQtGraph, maybe vispy
    #parser_run.add_argument('-p', '--plot', action="store_true", default=False,
    #                    help="live data plotting")
    parser_run.add_argument('-q', '--quiet', action="store_true", default=False,
                            help="no printed output")

    # read instrum.ini
    config = configparser.ConfigParser()
    config.read(INSTRUM_FILE)

    # execute
    user_args = parser.parse_args()
    user_args.func(user_args, config)

if __name__ == "__main__":
    # execute only if run as a script
    main()
