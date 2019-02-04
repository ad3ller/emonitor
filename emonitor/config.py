# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
from getpass import getpass
from collections.abc import Iterable
from configparser import ConfigParser

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
            self.write()

    def copy(self, existing, new, force=False, write=True):
        """ copy section `existing` to `new` (including defaults) """
        if not self.has_section(existing):
            raise NameError(f"{existing} not found in config file")
        if self.has_section(new):
            if force or input(f"{new} already exists. Overwrite (y/n) ?").lower() in ["y", "yes"]:
                self.remove_section(new)
            else:
                # abort
                return
        self.add_section(new)
        for option, value in self.items(existing):
            super().set(new, option, value=value)
        if write:
            self.write()

    def remove(self, instrum, force=False, write=True):
        """ remove section from the config file """
        prompt = f"Are you sure you want to remove {instrum} (y/n) ?"
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
            self.write()

    def set(self, instrum, option, value,
            encryption=None, force=False, write=True,
            list_options=["null_values"]):
        """ set attribute value(s) [with optional encryption] """
        # checks
        if not (instrum == "DEFAULT" or self.has_section(instrum)):
            raise NameError(f"{instrum} not found in config file")
        if encryption is None and not force and option in ["sql_passwd"]:
            prompt = f"Are you sure you want to store {option} without encryption (y/n) ?"
            if not input(prompt).lower() in ["y", "yes"]:
                return
        # user input
        if value is None:
            prompt = f"enter value for {instrum}.{option} :"
            if encryption is None:
                value = input(prompt)
            else:
                value = getpass(prompt=prompt, stream=sys.stderr)
        # squeeze
        if isinstance(value, Iterable) and len(value) == 1 and option not in list_options:
            value = value[0]
        # encrypt value
        if encryption is not None:
            assert hasattr(encryption, "encrypt"), "encryption object must have method `encrpyt`"
            value = encryption.encrypt(bytes(value, "utf-8")).decode("utf8")
        # set
        super().set(instrum, option, value=str(value))
        if write:
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
            self.write()

    def write(self, fil=None):
        """ overwrite instrum.ini """
        if fil is None:
            fil = self.fil
        with open(fil, "w+", encoding="utf8") as file_out:
            super().write(file_out)
