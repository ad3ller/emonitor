# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 21:55:57 2018

@author: adam
"""
import os
import datetime
import pandas as pd
from .core import DATA_DIRE

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
    template = "CREATE TABLE %s(`TIMESTAMP` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, %s)"
    sql = template%(table, ", ".join(['`' + str(c) + '` DOUBLE DEFAULT NULL' for c in columns]))
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()

def db_check(conn, table, columns, debug=False):
    """ check sqlite database
    """
    sql = "SELECT * FROM %s"%(table)
    if debug:
        print(sql)
    cursor = conn.cursor()
    cursor.execute(sql)
    db_columns = list(next(zip(*cursor.description)))
    for col in columns:
        if col not in db_columns:
            raise Exception("column %s not in sqlite database"%(col))
    cursor.close()

def db_insert(conn, table, columns, values, debug=False):
    """ INSERT INTO {table}({columns}) VALUES ({values});
    """
    values = ["'%s'"%v for v in values]
    columns = ["'%s'"%v for v in columns]
    sql = "INSERT INTO %s(%s) VALUES (%s)"%(table, ", ".join(columns), ", ".join(values))
    if debug:
        print(sql)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()

def tquery(conn, start=None, end=None, table='data', **kwargs):
    """ SELECT * FROM table WHERE tcol BETWEEN start AND end.

        If start is None, it will be set to time.now() - delta [default:
        4 hours], i.e., live mode.

        If end is None, set to start + delta, i.e., to select a given time
        window, specify either: start and end, or start and delta.

        If start and end are more than 24 hours apart, then a random
        sample of length specified by 'limit' is returned, unless
        'full_resolution' is set to True.

        args:
            table='data'  name of table in database     str
            start         query start time              datetime.datetime
            end           query end time                datetime.datetime

        kwargs:
            limit=6000               max number of rows               int
            tcol='TIMESTAMP'         timestamp column name            str
            delta=datetime.timedelta(hours=4)
                                     time to look back in live mode   datetime.timedelta
            full_resolution=False    No limit - return everything     bool
            coerce_float=True        convert, e.g., decimal to float  bool
            dropna=True              drop NULL columns                bool
            debug=False              print SQL query                  bool
        return:
            result       pandas.DataFrame
    """
    # read kwargs
    limit = kwargs.get('limit', 6000)
    tcol = kwargs.get('tcol', 'TIMESTAMP')
    delta = kwargs.get('delta', datetime.timedelta(hours=4))
    full_resolution = kwargs.get('full_resolution', False)
    coerce_float = kwargs.get('coerce_float', True)
    dropna = kwargs.get('dropna', True)
    debug = kwargs.get('debug', False)
    # check times
    start, end = get_trange(start, end, delta)
    # SQL query
    if full_resolution or limit is None:
        reorder = False
        sql = "SELECT * FROM `" + table + "` WHERE `" + tcol + "` BETWEEN '" + \
             start.strftime("%Y-%m-%d %H:%M:%S") + "' AND '" + \
             end.strftime("%Y-%m-%d %H:%M:%S") + "';"
    # check start and end are on the same day
    elif end - datetime.timedelta(days=1) < start:
        reorder = False
        sql = "SELECT * FROM `" + table + "` WHERE `" + tcol + "` BETWEEN '" + \
             start.strftime("%Y-%m-%d %H:%M:%S") + "' AND '" + \
             end.strftime("%Y-%m-%d %H:%M:%S") + "' LIMIT " + str(limit) + ";"
    else:
        # if time span is more than 1 day randomly sample measurements from range
        reorder = True
        sql = "SELECT * FROM `" + table + "` WHERE `" + tcol + "` BETWEEN '" + \
             start.strftime("%Y-%m-%d %H:%M:%S") + "' AND '" + \
             end.strftime("%Y-%m-%d %H:%M:%S") + "' ORDER BY RAND() LIMIT " + str(limit) + ";"
    if debug:
        print(sql)
    result = pd.read_sql_query(sql, conn, coerce_float=coerce_float, parse_dates=[tcol])
    if dropna:
        # remove empty columns
        result = result.dropna(axis=1, how='all')
    if reorder:
        # sort data by timestamp
        result = result.sort_values(by=tcol)
    result = result.set_index(tcol)
    return result

def get_trange(start, end, delta):
    """ Find start and end times from inputs.
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
                # niether start nor end specified -> live mode
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
