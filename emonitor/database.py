# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import os
import glob
import sqlite3
from humanize import naturalsize
from .core import TABLE, DATA_DIRE
from .tools import db_init, db_count, db_describe


def show_db_tables(args, config):
    '''  list sqlite database tables.
    '''
    fils = glob.glob(os.path.join(DATA_DIRE, '*.db'))
    if len(fils) == 0:
        print("No sqlite databases found.")
    else:
        fnames = [os.path.split(f)[1][:-3] for f in fils]
        print(fnames)


def describe_db(args, config):
    '''  describe sqlite database.
    '''
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if not os.path.isfile(fil):
        raise Exception("%s not found."%(fil))
    else:
        # info
        db = sqlite3.connect(fil)
        num_rows = db_count(db, TABLE)
        info = db_describe(db, TABLE)
        db.close()
        cols = [row[1] for row in info]
        # output
        print("path:", fil)
        print("size:", naturalsize(os.path.getsize(fil)))
        print("columns:", cols)
        print("rows:", "%d"%(num_rows))
        # schema
        if args.schema:
            print("schema:", "\n")
            for row in info:
                print(row)


def generate_db(args, config):
    ''' automatically create sqlite databases for configured instruments
    '''
    if len(args.instrums) == 0:
        args.instrums = config.sections()
    # check instrum exists
    for instrum in args.instrums:
        if not config.has_section(instrum):
            raise NameError("%s was not found in the config file"%(instrum))
        settings = dict(config.items(instrum))
        # database name
        if 'db' not in settings:
            raise NameError("'db' not configured for %s"%(instrum))
        db_name = settings['db']
        # get columns from instrument sensors
        if 'sensors' not in settings:
            raise NameError("'sensors' not configured for %s"%(instrum))
        if 'column_fmt' in settings:
            columns = tuple([settings['column_fmt'].replace('<sensor>', sen.strip()) for sen in settings['sensors'].split(',')])
        else:
            columns = tuple([sen.strip() for sen in settings['sensors'].split(',')])
        # sqlite database
        fil = os.path.join(DATA_DIRE, db_name + '.db')
        ## check existing
        if os.path.exists(fil) and args.overwrite:
            if args.force or input("Are you sure you want to permanently destroy existing %s (y/n) ?"%(fil)).lower() in ['y', 'yes']:
                os.remove(fil)
        ## create
        if not os.path.exists(fil):
            if not args.quiet:
                print(f"Creating {db_name}.db with columns {columns}")
            db = sqlite3.connect(fil)
            db_init(db, TABLE, columns)
            db.close()


def create_db(args, config):
    '''  create sqlite database.
    '''
    if not isinstance(args.columns, list):
        raise TypeError("Columns must be a list")
    db_name = args.db + '.db'
    fil = os.path.join(DATA_DIRE, db_name)
    if os.path.isfile(fil):
        if args.overwrite:
            os.remove(fil)
        else:
            raise Exception("Database already exists.  Use --overwrite.")
    if not args.quiet:
        print(f"Creating {db_name} with columns {tuple(args.columns)}")
    db = sqlite3.connect(fil)
    db_init(db, TABLE, args.columns)
    db.close()


def destroy_db(args, config):
    '''  delete sqlite database.
    '''
    fil = os.path.join(DATA_DIRE, args.db + '.db')
    if os.path.isfile(fil):
        if args.force or input("Are you sure you want to permanently destroy %s (y/n) ?"%(fil)).lower() in ['y', 'yes']:
            os.remove(fil)
    else:
        raise Exception("Failed to destory. Database not found.")
