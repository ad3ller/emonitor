# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import os
import sys
import logging
import sqlite3
from getpass import getpass
from ast import literal_eval
from importlib import import_module
from collections.abc import Iterable
from configparser import ConfigParser
import pymysql
from .core import DATA_DIRE
logger = logging.getLogger(__name__)


LIST_OPTIONS = ["sensors", "null_values", "columns"]


class EmonitorConfig(ConfigParser):
    """ view and edit instrum.ini file """
    def __init__(self, fil):
        super().__init__()
        self.fil = fil
        self.read(fil)

    def show(self, instrum=None):
        """ print [instrum] configuration """
        if instrum is None:
            super().write(sys.stdout)
        else:
            print(f"[{instrum}]")
            for option, value in self.items(instrum):
                print(f"{option} = {value}")

    def instruments(self):
        """ list instruments in config file """
        return self.sections()

    def new(self, instrum, force=False, write=True):
        """ create new section """
        if self.has_section(instrum):
            prompt = f"{instrum} already exists. Overwrite (y/n) ?"
            if force or input(prompt).lower() in ["y", "yes"]:
                self.remove_section(instrum)
            else:
                # abort
                return
        # update
        self.add_section(instrum)
        if write:
            logger.info(f"new(): instrum={instrum}")
            self.write()

    def copy(self, existing, new, defaults=False, force=False, write=True):
        """ copy section `existing` to `new` """
        if not self.has_section(existing):
            raise NameError(f"{existing} not found in config file")
        if self.has_section(new):
            if force or input(f"{new} already exists. Overwrite (y/n) ?").lower() in ["y", "yes"]:
                self.remove_section(new)
            else:
                # abort
                return
        logger.debug(f"copy(): add section {new}")
        self.add_section(new)
        if defaults:
            for option, value in self.items(existing):
                logger.debug(f"copy(): instrum={new}, {option}={value}")
                super().set(new, option, value=value)
        else:
            for option in self._sections[existing].keys():
                value = super().get(existing, option)
                logger.debug(f"copy(): instrum={new}, {option}={value}")
                super().set(new, option, value=value)
        if write:
            logger.info(f"copy(): existing={existing}, new={new}")
            self.write()

    def remove(self, instrum, force=False, write=True):
        """ remove section from the config file """
        prompt = f"Are you sure you want to remove {instrum} from the config file (y/n) ?"
        if not self.has_section(instrum):
            if instrum == "DEFAULT":
                raise NameError("Cannot remove DEFAULT section")
            else:
                raise NameError(f"{instrum} not found in config file")
        elif force or input(prompt).lower() in ["y", "yes"]:
            self.remove_section(instrum)
        else:
            # abort
            return
        if write:
            logger.info(f"remove(): instrum={instrum}")
            self.write()

    def get(self, instrum, option, encryption=None, **kwargs):
        """ get attribute value [with optional encryption] """
        value = super().get(instrum, option, **kwargs)
        if encryption is not None:
            assert hasattr(encryption, "decrypt"), "encryption object must have method `decrpyt`"
            logger.debug(f"get(): decrypt value")
            value = encryption.decrypt(bytes(value, "utf8")).decode("utf8")
        return value

    def set(self, instrum, option, value,
            encryption=None, force=False, write=True, **kwargs):
        """ set attribute value(s) [with optional encryption] """
        # checks
        list_options = kwargs.get("list_options", LIST_OPTIONS)
        if not (instrum == "DEFAULT" or self.has_section(instrum)):
            raise NameError(f"{instrum} not found in config file")
        if encryption is None and not force and option in ["sql_passwd"]:
            prompt = f"Are you sure you want to store {option} without encryption (y/n) ?"
            if not input(prompt).lower() in ["y", "yes"]:
                return
        # user input
        if value is None:
            logger.debug(f"set(): get user input")
            prompt = f"enter value for {instrum}.{option} :"
            if encryption is None:
                value = input(prompt)
            else:
                value = getpass(prompt=prompt, stream=sys.stderr)
        # squeeze
        if isinstance(value, Iterable) and len(value) == 1 and option not in list_options:
            logger.debug(f"set(): single value input")
            value = value[0]
        # encrypt value
        if encryption is not None:
            assert hasattr(encryption, "encrypt"), "encryption object must have method `encrpyt`"
            logger.debug(f"set(): encrypt value")
            value = encryption.encrypt(bytes(value, "utf-8")).decode("utf8")
        # set
        super().set(instrum, option, value=str(value), **kwargs)
        if write:
            logger.info(f"set(): instrum={instrum}, option={option}, value={value}")
            self.write()

    def drop(self, instrum, option, write=True):
        """ drop an attribute """
        if instrum == "DEFAULT" or self.has_section(instrum):
            if self.has_option(instrum, option):
                self.remove_option(instrum, option)
            else:
                raise NameError(f"{instrum}.{option} not found in config file")
        else:
            raise NameError(f"{instrum} not found in config file")
        if write:
            logger.info(f"drop(): instrum={instrum}, option={option}")
            self.write()

    def write(self, fil=None):
        """ overwrite instrum.ini """
        if fil is None:
            fil = self.fil
        with open(fil, "w+", encoding="utf8") as file_out:
            super().write(file_out)

    def eval_settings(self, instrum, exclude=None):
        """ read config section and use ast.literal_eval() to get python dtypes

        args:
            instrum           name of device
            exclude=None      list of keys excluded from ast.literal_eval()

        return:
            settings
        """
        settings = dict()
        # keys to ignore
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude]
        elif isinstance(exclude, Iterable):
            pass
        else:
            raise TypeError("arg `exclude` must be None, str or list")
        # evaluate items
        for key, value in self.items(instrum):
            if key in exclude:
                settings[key] = value
            else:
                try:
                    settings[key] = literal_eval(value)
                except:
                    settings[key] = value
        return settings

    def get_device(self, instrum):
        """ get device class """
        if self.has_option(instrum, "device_class"):
            device_class = self.get(instrum, "device_class")
        else:
            if instrum in ["simulate", "fake"]:
                device_class = "fake.Fake"
            else:
                device_class = "generic.Generic"
        # serial connection
        mod, obj = device_class.split(".")
        module = import_module("..devices." + mod, __name__)
        device = getattr(module, obj)
        return device

    def sqlite_connect(self, instrum, dire=DATA_DIRE):
        """ open connection to sqlite database """
        name = self.get(instrum, "db")
        fname, _ = os.path.splitext(name)
        fname += ".db"
        fil = os.path.join(dire, fname)
        if not os.path.isfile(fil):
            raise OSError(f"{fname} does not exists.  Use generate or create.")
        conn = sqlite3.connect(fil)
        logger.info(f"connected to sqlite database: fname={fname}")
        return conn

    def sql_connect(self, instrum, encryption=None):
        """ open connection to SQL database """
        # settings
        host = self.get(instrum, "sql_host")
        port = int(self.get(instrum, "sql_port"))
        database = self.get(instrum, "sql_db")
        # username
        if not self.has_option(instrum, "sql_user"):
            sql_user = input("SQL username : ")
        else:
            sql_user = self.get(instrum, "sql_user")
            print(f"SQL username : {sql_user}")
        # password
        if not self.has_option(instrum, "sql_passwd"):
            password = getpass(prompt="SQL password : ", stream=sys.stderr)
        elif encryption is not None:
            password = self.get(instrum, "sql_passwd", encryption=encryption)
        else:
            raise ValueError("cannot decrypt sql_passwd using encryption=None")
        # connect
        conn = pymysql.connect(host=host,
                               port=port,
                               user=sql_user,
                               password=password,
                               database=database)
        logger.info(f"connected to SQL server: host={host}, database={database}")
        return conn
