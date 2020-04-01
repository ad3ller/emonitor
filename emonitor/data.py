# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import os
import glob
import logging
import sqlite3
from collections.abc import Iterable
from humanize import naturalsize
from .core import TABLE
from .tools import (db_init,
                    db_count,
                    db_describe,
                    get_columns)
logger = logging.getLogger(__name__)


class EmonitorData(object):
    """ emonitor sqlite data directory """
    def __init__(self, dire):
        self.dire = dire

    def show(self):
        """ list sqlite database tables
        """
        fils = glob.glob(os.path.join(self.dire, "*.db"))
        fnames = [os.path.split(f)[1] for f in fils]
        return fnames

    def describe(self, name, schema=False):
        """  describe sqlite database
        """
        fname, _ = os.path.splitext(name)
        fname += ".db"
        fil = os.path.join(self.dire, fname)
        if not os.path.isfile(fil):
            raise OSError(f"{fil} not found")
        # info
        with sqlite3.connect(fil) as db:
            num_rows = db_count(db, TABLE)
            desc = db_describe(db, TABLE)
        columns = [row[1] for row in desc]
        # output
        info = {}
        info["file"] = fil
        info["size"] = naturalsize(os.path.getsize(fil))
        info["columns"] = columns
        info["rows"] = num_rows
        # schema
        if schema:
            info["schema"] = desc
        return info

    def create(self, name, columns, tcol="TIMESTAMP",
               dry_run=False, overwrite=False, quiet=False):
        """  create sqlite database
        """
        assert isinstance(columns, Iterable), "`columns` must be iterable"
        columns = tuple(columns)
        fname, _ = os.path.splitext(name)
        fname += ".db"
        fil = os.path.join(self.dire, fname)
        if os.path.isfile(fil):
            if overwrite:
                if not dry_run:
                    os.remove(fil)
            else:
                raise OSError("File already exists.  Use --overwrite.")
        if not quiet:
            print(f"Creating {fname} with columns : {columns}")
        logger.info(f"create(): fname={fname}, tcol={tcol}, columns={columns}")
        if not dry_run:
            with sqlite3.connect(fil) as db:
                db_init(db, TABLE, columns, tcol=tcol)

    def generate(self, config, instruments,
                 dry_run=False, overwrite=False, force=False, quiet=False):
        """ automatically create sqlite databases according to instrument configuration
        """
        if len(instruments) == 0:
            # generate for all sections
            instruments = config.sections()
        # check instrum exists
        num_new = 0
        for instrum in instruments:
            if not config.has_section(instrum):
                raise NameError(f"{instrum} not found in config file")
            tcol = config.get(instrum, "tcol", fallback="TIMESTAMP")
            # checks
            assert config.has_option(instrum, "db"), f"`db` not set for {instrum}"
            assert config.has_option(instrum, "sensors"), f"`sensors` not set for {instrum}"
            # database name
            name = config.get(instrum, "db")
            fname, _ = os.path.splitext(name)
            fname += ".db"
            settings = config.eval_settings(instrum)
            columns = get_columns(settings)
            # sqlite database
            fil = os.path.join(self.dire, fname)
            ## check existing
            if os.path.exists(fil) and overwrite:
                prompt = f"Are you sure you want to permanently destroy {fname} (y/n) ?"
                if force or input(prompt).lower() in ["y", "yes"]:
                    logger.debug(f"generate(), remove: {fil}")
                    if not dry_run:
                        os.remove(fil)
            ## create
            if not os.path.exists(fil):
                if not quiet:
                    print(f"Creating {fname} with columns {columns}")
                logger.info(f"generate(): fname={fname}, tcol={tcol}, columns={columns}")
                num_new += 1
                if not dry_run:
                    with sqlite3.connect(fil) as db:
                        db_init(db, TABLE, columns, tcol)
        logger.debug(f"generate(), number of new sqlite databases: {num_new}")

    def destroy(self, name, force=False):
        """  destroy sqlite database
        """
        fname, _ = os.path.splitext(name)
        fname += ".db"
        fil = os.path.join(self.dire, fname)
        if os.path.isfile(fil):
            prompt = f"Are you sure you want to permanently destroy {fname} (y/n) ?"
            if force or input(prompt).lower() in ["y", "yes"]:
                logger.info(f"destroy(): fil={fil}")
                os.remove(fil)
        else:
            raise OSError(f"{fname} not found")
