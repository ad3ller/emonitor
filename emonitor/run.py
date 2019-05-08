# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import time
import logging
import getpass
import sqlite3
from importlib import import_module
from cryptography.fernet import Fernet
import pymysql
from .core import (TABLE,
                   DATA_DIRE,
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


def get_sqlite(settings, columns):
    """ get sqlite connection """
    assert "db" in settings, "`db` not set in config"
    name = settings["db"]
    fname, _ = os.path.splitext(name)
    fname += ".db"
    fil = os.path.join(DATA_DIRE, fname)
    if not os.path.isfile(fil):
        raise OSError(f"{fname} does not exists.  Use generate or create.")
    db = sqlite3.connect(fil)
    logger.info(f"connected to SQLite database: fname={fname}")
    db_check(db, TABLE, columns)
    return db


def get_sql(settings):
    """ get connection to sql database """
    assert "sql_host" in settings, "sql_host not set in config"
    assert "sql_port" in settings, "sql_port not set in config"
    assert "sql_db" in settings, "sql_db not set in config"
    assert "sql_table" in settings, "sql_table not set in config"
    if "sql_user" not in settings:
        settings["sql_user"] = input("SQL username: ")
    else:
        print(f"SQL username: {settings['sql_user']}")
    if "sql_passwd" not in settings:
        prompt = f"Enter password: "
        sql_passwd = getpass.getpass(prompt=prompt, stream=sys.stderr)
    else:
        # decrypt password
        assert os.path.isfile(KEY_FILE), f"{KEY_FILE} not found.  Create using passwd."
        with open(KEY_FILE, "rb") as fil:
            key = fil.readline()
        fern = Fernet(key)
        sql_passwd = fern.decrypt(bytes(settings["sql_passwd"], "utf8")).decode("utf8")
    # connect
    sql_conn = pymysql.connect(host=settings["sql_host"],
                               port=int(settings["sql_port"]),
                               user=settings["sql_user"],
                               password=sql_passwd,
                               database=settings["sql_db"])
    logger.info(f"connected to SQL server: host={settings['sql_host']}, database={settings['sql_db']}")
    return sql_conn


def run(config, instrum, wait,
        output=False, sql=False, header=True, quiet=False):
    """ start the emonitor server and output to sqlite database.
    """
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
        db = get_sqlite(settings, columns) if output else None
        # sql output
        sql_conn = get_sql(settings) if sql else None
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
                                logger.warning(f"Failed to INSERT data into SQL database", exc_info=True)
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
