# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import time
import logging
from importlib import import_module
from cryptography.fernet import Fernet
from .core import (TABLE,
                   KEY_FILE)
from .tools import (db_check,
                    db_insert,
                    sql_insert,
                    get_columns,
                    parse_settings)
logger = logging.getLogger(__name__)


def get_device(settings, instrum):
    """ get instance of device_class """
    if "device_class" in settings:
        device_class = settings["device_class"]
    else:
        if instrum in ["simulate", "fake"]:
            device_class = "fake.Fake"
        else:
            device_class = "generic.Generic"
    # serial connection
    mod, obj = device_class.split(".")
    module = import_module("..devices." + mod, __name__)
    device = getattr(module, obj)(settings)
    return device


def run(config, instrum, wait,
        output=False, sql=False, header=True, quiet=False):
    """ run emonitor """
    tty = sys.stdout.isatty()
    settings = parse_settings(config, instrum)
    logger.info(f"start: instrum={instrum}, wait={wait}, output={output}, sql={sql}")
    logger.debug(f"{instrum} settings: {settings}")
    tcol = settings.get("tcol", "TIMESTAMP")
    columns = get_columns(settings, tcol)
    logger.debug(f"{instrum} columns: {columns}")
    try:
        device = get_device(settings, instrum)
        # sqlite output
        if output:
            db = config.sqlite_connect(instrum)
            db_check(db, TABLE, columns)
        else:
            db = None
        # sql output
        if sql:
            if config.has_option(instrum, "sql_passwd"):
                assert os.path.isfile(KEY_FILE)
                with open(KEY_FILE, "rb") as fil:
                    key = fil.readline()
                encryption = Fernet(key)
            else:
                encryption = None
            sql_conn = config.sql_connect(instrum, encryption=encryption)
        else:
            sql_conn = None
        # header
        if tty:
            if not quiet:
                print("Starting emonitor. Use Ctrl-C to stop. \n")
                if header:
                    str_width = 16
                    print(columns[0].rjust(19) +
                          "".join([c.rjust(str_width) for c in columns[1:]]))
        elif header:
            print(",".join(columns))
        num_db_errors = 0
        num_sql_errors = 0
        # start server
        while True:
            ## read data
            data = device.read_data()
            if data is not None:
                values = tuple(data)
                is_null = all([v is None for v in values])
                ## output
                if not is_null:
                    values = (time.strftime("%Y-%m-%d %H:%M:%S"), ) + values
                    if tty:
                        if not quiet:
                            val_str = tuple(str(v).replace("None", "NULL").rjust(str_width) for v in values)
                            print("".join(val_str))
                    else:
                        val_str = tuple(str(v).replace("None", "NULL") for v in values)
                        print(",".join(val_str))
                    if output:
                        try:
                            db_insert(db, TABLE, columns, values)
                            num_db_errors = 0
                        except:
                            num_db_errors += 1
                            if num_db_errors == 1:
                                # log first failure
                                logger.warning(f"Failed to INSERT data into {db}", exc_info=True)
                    if sql:
                        try:
                            if not sql_conn.open:
                                # attempt to reconnect
                                sql_conn.connect()
                            sql_insert(sql_conn, settings["sql_table"], columns, values)
                            num_sql_errors = 0
                        except:
                            num_sql_errors += 1
                            if num_sql_errors == 1:
                                # log first failure
                                logger.warning(f"Failed to INSERT data into SQL database",
                                               exc_info=True)
            time.sleep(wait)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logger.exception("Exception occurred")
        raise error
    finally:
        logger.info(f"stop")
        if tty and not quiet:
            print("\nStopping emonitor")
        device.close()
        if db is not None:
            db.close()
        if sql_conn is not None:
            sql_conn.close()
