# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import time
import logging
from cryptography.fernet import Fernet
from .core import (TABLE,
                   KEY_FILE)
from .tools import (db_check,
                    db_insert,
                    sql_insert,
                    get_columns,
                    format_commands)
logger = logging.getLogger(__name__)


def run(config, instrum, wait,
        output=False, output_skip=1, sql=False, sql_skip=1,
        header=True, quiet=False):
    """ run emonitor """
    tty = sys.stdout.isatty()
    settings = format_commands(config.eval_settings(instrum))
    logger.info(f"start: instrum={instrum}, wait={wait}, output={output}, sql={sql}")
    logger.debug(f"{instrum} settings: {settings}")
    tcol = settings.get("tcol", "TIMESTAMP")
    columns = get_columns(settings, tcol)
    logger.debug(f"{instrum} columns: {columns}")
    try:
        device = config.get_device(instrum)(settings)
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
        i = 0
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
                    if output and i % output_skip == 0:
                        try:
                            db_insert(db, TABLE, columns, values)
                            num_db_errors = 0
                        except:
                            num_db_errors += 1
                            if num_db_errors == 1:
                                # log first failure
                                logger.error(f"INSERT data into {db} failed", exc_info=True)
                    if sql and i % sql_skip == 0:
                        try:
                            if not sql_conn.open:
                                # attempt to reconnect after 10 failures
                                sql_conn.connect()
                            sql_insert(sql_conn, settings["sql_table"], columns, values)
                            num_sql_errors = 0
                        except:
                            num_sql_errors += 1
                            if num_sql_errors == 1:
                                # log first failure
                                logger.error(f"INSERT data into SQL database failed",
                                               exc_info=True)
            time.sleep(wait)
            i += 1
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
