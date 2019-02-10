# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 21:55:57 2018

@author: adam
"""
import os
import logging
import warnings
import sqlite3
import datetime
from collections.abc import Iterable
from ast import literal_eval
import numpy as np
import pandas as pd
from .core import DATA_DIRE
logger = logging.getLogger(__name__)


class CausalityError(ValueError):
    """ `There was an accident with a contraceptive and a time machine.`
    """
    pass


def db_path(name):
    """ Get path of sqlite file for 'name'.
    """
    fil = os.path.join(DATA_DIRE, name + '.db')
    return fil


def db_init(conn, table, columns):
    """ initialize sqlite database
    """
    column_str = ", ".join(['`' + str(c) + '` DOUBLE DEFAULT NULL' for c in columns])
    sql = f"CREATE TABLE {table}(`TIMESTAMP` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, {column_str});"
    logger.debug(f"db_init() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()


def db_check(conn, table, columns):
    """ check sqlite database
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
    """ count rows in sqlite table
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
    """
    col_str = str(tuple(columns)).replace("'", "`")
    val_str = ", ".join(tuple(r'%s' for c in columns))
    sql = f"INSERT INTO {table} {col_str} VALUES ({val_str});"
    logger.debug(f"sql_insert() sql: {sql}")
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()


def history(conn, start, end, **kwargs):
    """ SELECT * FROM table WHERE tcol BETWEEN start AND end.

        If start and end are more than 24 hours apart, then a random
        sample of length specified by 'limit' is returned, unless
        'full_resolution' is set to True.

        args:
            conn          database connection           object
            start         query start time              datetime.datetime / tuple / dict
            end           query end time                datetime.datetime / tuple / dict

        kwargs:
            table='data'             name of table in database        str
            limit=6000               max number of rows               int
            tcol='TIMESTAMP'         timestamp column name            str
            full_resolution=False    No limit - return everything     bool
            coerce_float=False       convert, e.g., decimal to float  bool
            dropna=True              drop NULL columns                bool
        return:
            result       pandas.DataFrame
    """
    # read kwargs
    table = kwargs.get('table', 'data')
    limit = kwargs.get('limit', 6000)
    tcol = kwargs.get('tcol', 'TIMESTAMP')
    full_resolution = kwargs.get('full_resolution', False)
    coerce_float = kwargs.get('coerce_float', False)
    dropna = kwargs.get('dropna', True)
    # start
    if isinstance(start, datetime.datetime):
        pass
    elif isinstance(start, tuple):
        start = datetime.datetime(*start)
    elif isinstance(start, dict):
        start = datetime.datetime(**start)
    else:
        raise TypeError("type(start) must be in [datetime.dateime, tuple, dict].")
    # end
    if isinstance(end, datetime.datetime):
        pass
    elif isinstance(end, tuple):
        end = datetime.datetime(*end)
    elif isinstance(start, dict):
        end = datetime.datetime(**end)
    else:
        raise TypeError("type(end) must be in [datetime.dateime, tuple, dict].")
    # check times
    if end < start:
        raise CausalityError('end before start')
    # connection type
    if isinstance(conn, sqlite3.Connection):
        rand = "RANDOM()"
    else:
        rand = "RAND()"
    # SQL query
    if full_resolution or limit is None:
        reorder = False
        sql = f"SELECT * FROM `{table}` WHERE `{tcol}` BETWEEN '{start}' AND '{end}';"
    # check start and end are on the same day
    elif end - datetime.timedelta(days=1) < start:
        reorder = False
        sql = f"SELECT * FROM `{table}` WHERE `{tcol}` BETWEEN '{start}' AND '{end}' LIMIT {limit};"
    else:
        # if time span is more than 1 day randomly sample measurements from range
        reorder = True
        sql = f"SELECT * FROM `{table}` WHERE `{tcol}` BETWEEN '{start}' AND '{end}' ORDER BY {rand} LIMIT {limit};"
    logger.debug(f"history() sql: {sql}")
    result = pd.read_sql_query(sql, conn, coerce_float=coerce_float, parse_dates=[tcol])
    if len(result.index) > 0:
        result.replace("NULL", np.nan, inplace=True)
        if dropna:
            # remove empty columns
            result = result.dropna(axis=1, how='all')
        if reorder:
            # sort data by timestamp
            result = result.sort_values(by=tcol)
        result = result.set_index(tcol)
    return result


def live(conn, delta=None, **kwargs):
    """ SELECT * FROM table WHERE tcol BETWEEN (time.now() - delta) AND time.now().

        If delta is more than 24 hours then a random sample of length specified
        by 'limit' is returned, unless 'full_resolution' is set to True.

        args:
            conn          database connection           object
            delta         query start time              datetime.timedelta / dict

        kwargs:
            table='data'             name of table in database        str
            limit=6000               max number of rows               int
            tcol='TIMESTAMP'         timestamp column name            str
            full_resolution=False    No limit - return everything     bool
            coerce_float=True        convert, e.g., decimal to float  bool
            dropna=True              drop NULL columns                bool
        return:
            result       pandas.DataFrame

    """
    if delta is None:
        delta = {"hours" : 4}
    if isinstance(delta, datetime.timedelta):
        pass
    elif isinstance(delta, dict):
        delta = datetime.timedelta(**delta)
    else:
        raise TypeError("type(delta) must be in [datetime.timedelta, dict].")
    end = datetime.datetime.now()
    start = end - delta
    return history(conn, start, end, **kwargs)


def tquery(conn, start=None, end=None, **kwargs):
    """ ------------------------------------------------------------
        DeprecationWarning
            Use history() or live() instead.
        ------------------------------------------------------------

        SELECT * FROM table WHERE tcol BETWEEN start AND end.

        If start is None, it will be set to time.now() - delta [default:
        4 hours], i.e., live mode.

        If end is None, set to start + delta, i.e., to select a given time
        window, specify either: start and end, or start and delta.

        If start and end are more than 24 hours apart, then a random
        sample of length specified by 'limit' is returned, unless
        'full_resolution' is set to True.

        args:
            conn          database connection           object
            start         query start time              datetime.datetime
            end           query end time                datetime.datetime

        kwargs:
            delta=datetime.timedelta(hours=4)
                                     time to look back in live mode   datetime.timedelta
            table='data'             name of table in database        str
            limit=6000               max number of rows               int
            tcol='TIMESTAMP'         timestamp column name            str
            full_resolution=False    No limit - return everything     bool
            coerce_float=True        convert, e.g., decimal to float  bool
            dropna=True              drop NULL columns                bool
        return:
            result       pandas.DataFrame
    """
    warnings.warn("tquery() is deprecated. Use history() or live() instead.", DeprecationWarning)
    # read kwargs
    delta = kwargs.get('delta', datetime.timedelta(hours=4))
    start, end = get_trange(start, end, delta)
    result = history(conn, start, end, **kwargs)
    return result


def get_trange(start, end, delta):
    """ find start and end times from inputs
    """
    if not isinstance(start, datetime.datetime) or not isinstance(end, datetime.datetime):
        # start or end unspecified -> delta required
        if not isinstance(delta, datetime.timedelta):
            # check delta type
            raise TypeError('delta must be of type datetime.timedelta')
        # check whether start or end is missing
        if not isinstance(start, datetime.datetime):
            # start not specified, check end
            if not isinstance(end, datetime.datetime):
                # neither start nor end specified -> live mode
                end = datetime.datetime.now()
            # infer start from end and delta
            start = end - delta
        if not isinstance(end, datetime.datetime):
            # infer end from start and delta
            end = start + delta
    # all good?
    if end < start:
        raise CausalityError('end before start')
    return start, end


def format_commands(settings):
    """ format string commands
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


def parse_settings(conf, instrum, ignore=None):
    """ read config section and use ast.literal_eval() to get python dtypes
    """
    settings = dict()
    # keys to ignore
    if ignore is None:
        ignore = []
    if not isinstance(ignore, Iterable):
        ignore = [ignore]
    # evaluate items
    for key, value in conf.items(instrum):
        if key in ignore:
            settings[key] = value
        else:
            try:
                settings[key] = literal_eval(value)
            except:
                settings[key] = value
    return format_commands(settings)
