# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import argparse
import logging
from pprint import pprint
from .core import INSTRUM_FILE, LOG_FILE, KEY_FILE, DATA_DIRE
from .encryption import fernet_key
from .data import EmonitorData
from .config import EmonitorConfig
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
    """

def main():
    """ run emonitor as a script """
    # read instrum.ini
    config = EmonitorConfig(INSTRUM_FILE)
    data = EmonitorData(DATA_DIRE)
    # user input
    parser = argparse.ArgumentParser(description="emonitor",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(title="command",
                                       dest="command",
                                       description=DESCRIPTION)
    subparsers.required = True

    # list instruments
    parser_ls = subparsers.add_parser("list", aliases=["ls"])
    parser_ls.set_defaults(func=config.instruments)

    # show config
    parser_show = subparsers.add_parser("config")
    parser_show.set_defaults(func=config.show)
    parser_show.add_argument("instrum", type=str, nargs="?", default=None,
                             help="serial device name [if None then show all]")

    # new instrument
    parser_new = subparsers.add_parser("new")
    parser_new.set_defaults(func=config.new)
    parser_new.add_argument("instrum", type=str, help="new device name")
    parser_new.add_argument("--force", action="store_true", default=False,
                            help="ignore warnings")

    # copy instrument
    parser_copy = subparsers.add_parser("copy", aliases=["cp"])
    parser_copy.set_defaults(func=config.copy)
    parser_copy.add_argument("existing", type=str, help="existing device name")
    parser_copy.add_argument("new", type=str, help="new device name")
    parser_copy.add_argument("--force", action="store_true", default=False,
                             help="ignore warnings")

    # remove instrument
    parser_delete = subparsers.add_parser("remove", aliases=["rm"])
    parser_delete.set_defaults(func=config.remove)
    parser_delete.add_argument("instrum", type=str, help="device name")
    parser_delete.add_argument("--force", action="store_true", default=False,
                               help="ignore warnings")

    # set attrib
    parser_set = subparsers.add_parser("set")
    parser_set.set_defaults(func=config.set)
    parser_set.add_argument("instrum", type=str, nargs="?", default="DEFAULT",
                            help="device name [if None then DEFAULT]")
    parser_set.add_argument("-k", "--key", dest="option", required=True,
                            help="attribute key, e.g., port")
    parser_set.add_argument("-v", "--value", nargs="+",
                            help="attribute value, e.g., COM7")
    parser_set.add_argument("--force", action="store_true", default=False,
                            help="ignore warnings")

    # remove attrib
    parser_drop = subparsers.add_parser("drop")
    parser_drop.set_defaults(func=config.drop)
    parser_drop.add_argument("instrum", type=str, nargs="?", default="DEFAULT",
                             help="device name [if None then DEFAULT]")
    parser_drop.add_argument("-k", "--key", dest="option", required=True,
                             help="attribute key, e.g., port")

    # set encrypted
    parser_passwd = subparsers.add_parser("passwd")
    parser_passwd.set_defaults(func=config.set, value=None, encryption=fernet_key(KEY_FILE))
    parser_passwd.add_argument("instrum", type=str, default="DEFAULT",
                               help="device name [if None then DEFAULT]")
    parser_passwd.add_argument("-k", "--key", dest="option", default="sql_passwd",
                               help="attribute key, e.g., sql_passwd")

    # list sqlite database tables
    parser_show = subparsers.add_parser("show")
    parser_show.set_defaults(func=data.show)

    # describe sqlite3 database
    parser_describe = subparsers.add_parser("describe")
    parser_describe.set_defaults(func=data.describe)
    parser_describe.add_argument("name", type=str, help="database name")
    parser_describe.add_argument("-s", "--schema", action="store_true", default=False,
                                 help="table structure")

    # create sqlite3 database
    parser_create = subparsers.add_parser("create")
    parser_create.set_defaults(func=data.create)
    parser_create.add_argument("name", type=str, help="database name")
    parser_create.add_argument("-c", "--columns", nargs="+", required=True, help="table column(s)")
    parser_create.add_argument("-q", "--quiet", action="store_true", default=False,
                               help="no printed output")
    parser_create.add_argument("--overwrite", action="store_true", default=False,
                               help="overwrite existing")

    # auto-create sqlite3 database
    parser_generate = subparsers.add_parser("generate")
    parser_generate.set_defaults(func=data.generate, config=config)
    parser_generate.add_argument("instruments", nargs="*",
                                 help="device name(s) [if None then all].")
    parser_generate.add_argument("-q", "--quiet", action="store_true", default=False,
                                 help="no printed output")
    parser_generate.add_argument("--overwrite", action="store_true", default=False,
                                 help="overwrite existing")
    parser_generate.add_argument("--force", action="store_true", default=False,
                                 help="ignore warnings")

    # destroy sqlite3 database
    parser_destroy = subparsers.add_parser("destroy")
    parser_destroy.set_defaults(func=data.destroy)
    parser_destroy.add_argument("name", type=str, help="database name")
    parser_destroy.add_argument("--force", action="store_true", default=False,
                                help="ignore warnings")

    # run server
    parser_run = subparsers.add_parser("run")
    parser_run.set_defaults(func=run, config=config)
    parser_run.add_argument("instrum", type=str, help="serial device name")
    parser_run.add_argument("--debug", action="store_true", default=False,
                            help="enable debugging info")
    parser_run.add_argument("-o", "--output", action="store_true", default=False,
                            help="enable SQLite output")
    parser_run.add_argument("-s", "--sql", action="store_true", default=False,
                            help="enable output to SQL server output")
    parser_run.add_argument("-w", "--wait", type=float, default=15.0,
                            help="wait time (s) between queries")
    parser_run.add_argument("-n", "--no_header", dest="header", action="store_false", default=True,
                            help="don't print header, e.g., when appending to a file")
    # TODO probably PyQtGraph, maybe vispy
    #parser_run.add_argument("-p", "--plot", action="store_true", default=False,
    #                    help="live data plotting")
    parser_run.add_argument("-q", "--quiet", action="store_true", default=False,
                            help="no printed output")

    # format user input
    user_args = parser.parse_args()
    args = dict(vars(user_args))
    args.pop("command")
    func = args.pop("func")
    debug = args.pop("debug", False)

    # logging
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(name)s %(message)s")
    else:
        logging.basicConfig(filename=LOG_FILE,
                            level=logging.INFO,
                            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    # execute
    response = func(**args)
    if response is not None:
        pprint(response)

if __name__ == "__main__":
    # execute only if run as a script
    main()
