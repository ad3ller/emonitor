# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 21:55:57 2018

@author: adam
"""
import os
import logging
import sqlite3
import datetime
import pytz
from collections.abc import Iterable
import numpy as np
import pandas as pd
from .core import DATA_DIRE, TMP_DIRE
logger = logging.getLogger(__name__)


class CausalityError(ValueError):
    """ `There was an accident with a contraceptive and a time machine.`
    """
    pass


def db_path(name, live=False):
    """ build path of SQLite database file

    args:
        name         database name        str

    return:
        fil
    """
    fname, _ = os.path.splitext(name)
    if live:
        fname += ".live.db"
        fil = os.path.join(TMP_DIRE, fname)
    else:
        fname += ".db"
        fil = os.path.join(DATA_DIRE, fname)
    return fil


def db_remove(conn, table):
    """ remove SQLite table

    args:
        conn               connection to db
        table              name of the table
    """
    sql = f"DROP TABLE {table};"
    logger.debug(f"db_remove() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()

def db_init(conn, table, columns, tcol="TIMESTAMP"):
    """ initialize SQLite database

    args:
        conn               connection to db
        table              name of the table
        columns            list of columns (excl. tcol)

    kwargs:
        tcol='TIMESTAMP'   name of timestamp column
    """
    cursor = conn.cursor()
    # initialize
    column_str = ", ".join(['`' + str(c) + '` DOUBLE DEFAULT NULL' for c in columns])
    sql = f"CREATE TABLE {table}(`{tcol}` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, {column_str});"
    logger.debug(f"db_init() sql: {sql}")
    cursor.execute(sql)
    cursor.close()


def db_limit_rows(conn, table, num, tcol="TIMESTAMP"):
    """ Add SQLite database trigger

    args:
        conn               connection to db
        table              name of the table
        num                max number of rows

    kwargs:
        tcol='TIMESTAMP'   name of timestamp column
    """
    cursor = conn.cursor()
    sql = f"""CREATE TRIGGER limit_rows INSERT ON {table}
              BEGIN
              DELETE FROM {table} WHERE rowid NOT IN (SELECT rowid FROM {table} ORDER BY {tcol} DESC LIMIT {num});
              END;
           """
    logger.debug(f"db_limit_rows() sql: {sql}")
    cursor.execute(sql)
    cursor.close()


def db_limit_time(conn, table, num, tcol="TIMESTAMP"):
    """ Add SQLite database trigger

    args:
        conn               connection to db
        table              name of the table
        num                max number of days

    kwargs:
        tcol='TIMESTAMP'   name of timestamp column
    """
    cursor = conn.cursor()
    sql = f"""CREATE TRIGGER limit_days INSERT ON {table}
              BEGIN
              DELETE FROM {table} WHERE {tcol} <= datetime('now','-{num} days', 'UTC');
              END;
           """
    logger.debug(f"db_limit_days() sql: {sql}")
    cursor.execute(sql)
    cursor.close()


def db_check(conn, table, columns):
    """ check columns all exist in SQLite database

    args:
        conn               connection to db
        table              name of the table
        columns            list of columns
    """
    sql = f"SELECT * FROM {table};"
    logger.debug(f"db_check() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql)
    db_columns = list(next(zip(*cursor.description)))
    logger.debug(f"db_check() columns: {db_columns}")
    for col in columns:
        if col not in db_columns:
            cursor.close()
            conn.close()
            raise NameError(f"columnn `{col}` not in sqlite database")
    cursor.close()


def db_count(conn, table):
    """ count rows in SQLite table

    args:
        conn               connection to db
        table              name of the table

    return:
        number of rows
    """
    sql = f"SELECT COUNT(*) as count FROM {table};"
    logger.debug(f"db_count() sql: {sql}")
    cursor = conn.cursor()
    response = cursor.execute(sql).fetchone()
    logger.debug(f"db_count() response: {response}")
    num_rows = response[0]
    cursor.close()
    return num_rows


def db_describe(conn, table):
    """ get sqlite database structure

    args:
        conn               connection to db
        table              name of the table

    return:
        info
    """
    sql = f"PRAGMA table_info({table});"
    logger.debug(f"db_describe() sql: {sql}")
    cursor = conn.cursor()
    info = cursor.execute(sql).fetchall()
    logger.debug(f"db_describe() info: {info}")
    cursor.close()
    return info


def db_insert(conn, table, columns, values):
    """ INSERT INTO {table} {columns} VALUES {values};

    args:
        conn               connection to SQLite db
        table              name of the table
        columns            list of columns
        values             list of values
    """
    col_str = str(tuple(columns)).replace("'", "`")
    val_str = ", ".join(tuple('?' for c in columns))
    sql = f"INSERT INTO {table} {col_str} VALUES ({val_str});"
    logger.debug(f"db_insert() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()


def sql_insert(conn, table, columns, values):
    """ INSERT INTO {table} {columns} VALUES {values};

    args:
        conn               connection to SQL server
        table              name of the table
        columns            list of columns
        values             list of values
    """
    col_str = str(tuple(columns)).replace("'", "`")
    val_str = ", ".join(tuple(r'%s' for c in columns))
    sql = f"INSERT INTO {table} {col_str} VALUES ({val_str});"
    logger.debug(f"sql_insert() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()


def get_columns(settings, tcol="TIMESTAMP"):
    """ get columns from sensor names

    Order of preference for extracting columns from settings:

        1) settings['columns']
        2) replace {sensor} in settings['column_fmt'] with
           each of settings['sensors']
        3) settings['sensors']

    args:
        settings           dict() of settings

    kwargs:
        tcol='TIMESTAMP'   name of timestamp column

    return:
        list of columns
    """
    sensors = settings["sensors"]
    assert isinstance(sensors, Iterable), "`sensors` must be iterable"
    if "columns" in settings:
        columns = tuple(settings["columns"])
    elif "column_fmt" in settings:
        column_fmt = settings["column_fmt"]
        columns = tuple([column_fmt.replace("{sensor}", str(sen).strip()) for sen in sensors])
    else:
        columns = tuple([str(sen).strip() for sen in sensors])
    assert len(columns) == len(sensors), "number of sensors and output columns mismatched"
    if tcol is not None:
        columns = (tcol,) + columns
    return columns


def format_commands(settings):
    """ format string commands

    Replace special characters ["$CR", "$LF", "$ACK", "$ENQ"]
    in settings['cmd', 'ack', 'enq'].

    args:
        settings           dict() of settings

    return:
        modified settings
    """
    for key in ['cmd', 'ack', 'enq']:
        if key in settings:
            value = settings[key]
            if isinstance(value, str):
                # string replacements
                for placeholder, replacement in [("$CR", "\x0D"),
                                                 ("$LF", "\x0A"),
                                                 ("$ACK", "\x06"),
                                                 ("$ENQ", "\x05")]:
                    if placeholder in value:
                        value = value.replace(placeholder, replacement)
                settings[key] = value
    return settings


def history(conn, start, end, **kwargs):
    """ SELECT * FROM table WHERE tcol BETWEEN start AND end.

    If start and end are more than 24 hours apart, then a random
    sample of length specified by 'limit' is returned.

    data is assumed to be stored in with UTC timestamps

    unaware datetimes for args start / end default to UTC unless tz is set

    args:
        conn          database connection           object
        start         query start time              datetime.datetime / tuple / dict / str
        end           query end time                datetime.datetime / tuple / dict / str
                                                    str format: '%Y-%m-%d %H:%M:%S'

    kwargs:
        table='data'             name of table in database           str
        limit=6000               max number of rows                  int or None
        tcol='TIMESTAMP'         timestamp column name               str
        tz=None                  timezone for start / end and data   str or None (e.g, 'CET')
        coerce_float=False       convert, e.g., decimal to float     bool
        dropna=True              drop NULL columns                   bool

    return:
        result         pandas.DataFrame
    """
    # read kwargs
    table = kwargs.get('table', 'data')
    limit = kwargs.get('limit', 6000)
    tcol = kwargs.get('tcol', 'TIMESTAMP')
    tz = kwargs.get('tz', None)
    coerce_float = kwargs.get('coerce_float', False)
    dropna = kwargs.get('dropna', True)
    ascending = kwargs.get('ascending', True)
    # start
    if isinstance(start, datetime.datetime):
        if start.tzinfo is not None:
            start = start.astimezone(pytz.utc)
    elif isinstance(start, tuple):
        start = datetime.datetime(*start)
    elif isinstance(start, dict):
        start = datetime.datetime(**start)
    elif isinstance(start, str):
        start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    else:
        raise TypeError("type(start) must be in [datetime.dateime, tuple, dict, str].")
    # end
    if isinstance(end, datetime.datetime):
        if end.tzinfo is not None:
            end = end.astimezone(pytz.utc)
    elif isinstance(end, tuple):
        end = datetime.datetime(*end)
    elif isinstance(end, dict):
        end = datetime.datetime(**end)
    elif isinstance(end, str):
        end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
    else:
        raise TypeError("type(end) must be in [datetime.dateime, tuple, dict, str].")
    # set timezone
    if tz is not None:
        timezone = pytz.timezone(tz)
        if start.tzinfo is None:
            start = timezone.localize(start).astimezone(pytz.utc)
        if end.tzinfo is None:
            end = timezone.localize(end).astimezone(pytz.utc)
    # check times
    if end < start:
        raise CausalityError('end before start')
    # connection type
    if isinstance(conn, sqlite3.Connection):
        rand = "RANDOM()"
    else:
        rand = "RAND()"
    # SQL query
    if limit is None:
        reorder = False
        sql = f"SELECT * FROM `{table}` WHERE `{tcol}` BETWEEN '{start}' AND '{end}';"
    else:
        # random sample from range
        reorder = True
        sql = f"SELECT * FROM `{table}` WHERE `{tcol}` BETWEEN '{start}' AND '{end}' ORDER BY {rand} LIMIT {limit};"
    logger.debug(f"history() sql: {sql}")
    result = pd.read_sql_query(sql, conn, coerce_float=coerce_float, parse_dates={tcol:{'utc':True}})
    if len(result.index) > 0:
        logger.debug(f"history() num_rows: {len(result.index)}")
        result.replace("NULL", np.nan, inplace=True)
        if dropna:
            # remove empty columns
            result = result.dropna(axis=1, how='all')
        if reorder or not ascending:
            # sort data by timestamp
            result = result.sort_values(by=tcol, ascending=ascending)
        if tz is not None:
            result[tcol] = result[tcol].dt.tz_convert(tz)
        result = result.set_index(tcol)
    return result


def live(conn, delta=None, **kwargs):
    """ SELECT * FROM table WHERE tcol BETWEEN (time.now() - delta) AND time.now().

    If delta is more than 24 hours then a random sample of length specified
    by 'limit' is returned.

    args:
        conn          database connection           object
        delta         query start time              datetime.timedelta / dict

    kwargs:
        table='data'             name of table in database        str
        limit=6000               max number of rows               int or None
        tcol='TIMESTAMP'         timestamp column name            str
        tz=None                  timezone
        coerce_float=True        convert, e.g., decimal to float  bool
        dropna=True              drop NULL columns                bool

    return:
        result         pandas.DataFrame
    """
    if delta is None:
        delta = {"hours" : 4}
    if isinstance(delta, datetime.timedelta):
        pass
    elif isinstance(delta, dict):
        delta = datetime.timedelta(**delta)
    else:
        raise TypeError("type(delta) must be in [datetime.timedelta, dict].")
    end = datetime.datetime.now(tz=pytz.utc)
    start = end - delta
    return history(conn, start, end, **kwargs)
