# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import time
import warnings
import getpass
import sqlite3
from importlib import import_module
import pymysql
from cryptography.fernet import Fernet
from .core import (TABLE,
                   DATA_DIRE,
                   KEY_FILE)
from .tools import (db_check,
                    db_insert,
                    parse_settings)


def run(args, config):
    """ start the emonitor server and output to sqlite database.
    """
    tty = sys.stdout.isatty()
    header = not args.no_header
    settings = parse_settings(config, args.instrum)
    if 'column_fmt' in settings:
        column_fmt = settings['column_fmt']
        columns = ('TIMESTAMP',) + tuple([column_fmt.replace("{sensor}", str(sen).strip()) for sen in settings['sensors']])
    else:
        columns = ('TIMESTAMP',) + tuple([str(sen).strip() for sen in settings['sensors']])
    db = None
    sql_conn = None
    debug = args.debug
    if debug and tty:
        print("DEBUG enabled")
        print(settings)
    try:
        # simulate
        if "device_class" not in settings:
            if args.instrum in ["simulate", "fake"]:
                settings["device_class"] = "fake.Fake"
            else:
                settings["device_class"] = "generic.Generic"
        # serial connection
        mod, obj = settings["device_class"].split('.')
        module = import_module("..devices." + mod, __name__)
        instrum = getattr(module, obj)(settings, debug=debug)
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
                settings['sql_user'] = input('SQL username: ')
            else:
                print(f"SQL username: {settings['sql_user']}")
            if 'sql_passwd' not in settings:
                prompt = f"Enter password: "
                sql_passwd = getpass.getpass(prompt=prompt, stream=sys.stderr)
            else:
                # decrypt password
                assert os.path.isfile(KEY_FILE), f"{KEY_FILE} not found.  Create using passwd."
                with open(KEY_FILE, "rb") as fil:
                    key = fil.readline()
                fern = Fernet(key)
                sql_passwd = fern.decrypt(bytes(settings['sql_passwd'], 'utf8')).decode('utf8')
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
                    test = instrum.read_data(debug=debug)
                    if debug:
                        print(test)
                    str_width = len(str(test[0]))
                    print(columns[0].rjust(19) + ' \t', '\t '.join([col.rjust(str_width) for col in columns[1:]]))
        elif header:
            print(', '.join(columns))
        # start server
        while True:
            ## read data
            values = instrum.read_data(debug=debug)
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
                    try:
                        db_insert(sql_conn, settings['sql_table'], columns, values, debug=debug)
                    except:
                        warnings.warn("SQL connection failed")
                        # attempt to reconnect
                        try:
                            sql_conn = pymysql.connect(host=settings['sql_host'],
                                                       port=int(settings['sql_port']),
                                                       user=settings['sql_user'],
                                                       password=sql_passwd,
                                                       database=settings['sql_db'])
                        except:
                            pass
            ## reset
            time.sleep(args.wait)
    except KeyboardInterrupt:
        # stop server
        if tty and not args.quiet:
            print('\nStopping emonitor.')
    finally:
        # clean up
        instrum.close()
        if db is not None:
            db.close()
        if sql_conn is not None:
            sql_conn.close()
