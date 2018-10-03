# -*- coding: utf-8 -*-
"""
Created on Mon July 9 22:20:12 2018

@author: Adam
"""
import os
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from emonitor.core import TABLE, DATA_DIRE
from emonitor.tools import db_path, db_init, db_check, db_describe, db_insert, tquery, history

# constants
COLUMNS = ('A', 'B', 'C')
TCOL = 'TIMESTAMP'
DB = db_path('__pytest__.db')
if os.path.exists(DB):
    os.remove(DB)
CONN = sqlite3.connect(DB)
DATA = [('2016-12-09 09:08:13', 1, 34.8, 3),
        ('2018-12-10 09:08:13', 2, 12, 3),
        ('2018-12-10 09:10:13', 3, 6.7, 3)]

def test_datadire_exists():
    assert os.path.exists(DATA_DIRE)

def test_new_db():
    db_init(CONN, TABLE, COLUMNS)
    db_check(CONN, TABLE, COLUMNS)

def test_desc():
    DESC = "[(0, 'TIMESTAMP', 'timestamp', 1, 'CURRENT_TIMESTAMP', 0), (1, 'A', 'DOUBLE', 0, 'NULL', 0), (2, 'B', 'DOUBLE', 0, 'NULL', 0), (3, 'C', 'DOUBLE', 0, 'NULL', 0)]"
    assert str(db_describe(CONN, TABLE)) == DESC

def test_insert():
    cols = (TCOL,) + COLUMNS
    for d in DATA:
        db_insert(CONN, TABLE, cols, d)

def test_tquery():
    start = datetime(2015, 12, 9, 9, 8, 13)
    end = datetime(2018, 12, 11, 9, 8, 13)
    df = tquery(CONN, start, end)
    vals = np.array([row[1:] for row in DATA])
    assert np.array_equal(df.values, vals)

def test_history():
    start = datetime(2015, 12, 9, 9, 8, 13)
    end = datetime(2018, 12, 11, 9, 8, 13)
    df = history(CONN, start, end)
    vals = np.array([row[1:] for row in DATA])
    assert np.array_equal(df.values, vals)

def test_clean():
    CONN.close()
    os.remove(DB)
