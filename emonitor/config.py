# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 13:43:09 2017

@author: Adam
"""
import sys
import os
import getpass
from cryptography.fernet import Fernet
from .core import INSTRUM_FILE, KEY_FILE


def overwrite(config):
    """ save instrum.ini """
    with open(INSTRUM_FILE, 'w+', encoding='utf8') as fil:
        config.write(fil)


def list_instruments(args, config):
    """ list sections in the config file """
    print(config.sections())


def new_instrument(args, config):
    """ create a new configuration section """
    if config.has_section(args.output):
        if input("%s already exists. Overwrite (y/n) ?"%(args.output)).lower() in ['y', 'yes']:
            config.remove_section(args.output)
        else:
            sys.exit()
    config.add_section(args.output)
    overwrite(config)


def copy_instrument(args, config):
    """ copy config sections args.instrum to args.output (including any defaults)"""
    if not config.has_section(args.instrum):
        raise NameError("%s was not found in the config file"%(args.instrum))
    elif config.has_section(args.output):
        if args.force or input("%s already exists. Overwrite (y/n):"%(args.output)).lower() in ['y', 'yes']:
            config.remove_section(args.output)
        else:
            # abort
            sys.exit()
    config.add_section(args.output)
    for key, value in config.items(args.instrum):
        config.set(args.output, key, value)
    overwrite(config)


def delete_instrument(args, config):
    """ delete a section of the config file """
    if not config.has_section(args.instrum):
        if args.instrum == 'DEFAULT':
            raise Exception("Cannot remove DEFAULT section from instrum.ini")
        else:
            raise NameError("%s was not found in the config file"%(args.instrum))
    elif args.force or input("Are you sure you want to delete %s (y/n) ?"%(args.instrum)).lower() in ['y', 'yes']:
        # delete file
        config.remove_section(args.instrum)
        overwrite(config)
    else:
        # abort
        sys.exit()


def set_instrument_attribute(args, config):
    """ set an instrument attribute """
    if args.key == "sql_passwd":
        raise ValueError("Use passwd tool to store passwords.")
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        if len(args.value) == 1:
            config.set(args.instrum, args.key, str(args.value[0]))
        else:
            config.set(args.instrum, args.key, str(args.value))
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show_config(args, config)
    overwrite(config)


def drop_instrument_attribute(args, config):
    """ drop an instrument attribute """
    if args.instrum == 'DEFAULT' or config.has_section(args.instrum):
        if config.has_option(args.instrum, args.key):
            config.remove_option(args.instrum, args.key)
        else:
            raise NameError("%s.%s was not found in the config file"%(args.instrum, args.key))
    else:
        raise NameError("%s was not found in the config file"%(args.instrum))
    if args.print:
        show_config(args, config)
    overwrite(config)


def show_config(args, config):
    """ print instrument configuration """
    if args.instrum == '__all__':
        config.write(sys.stdout)
    else:
        print('[%s]'%(args.instrum))
        for key, value in config.items(args.instrum):
            print('%s = %s'%(key, value))


def passwd(args, config):
    """ store SQL password.
    """
    if args.instrum != 'DEFAULT' and not config.has_section(args.instrum):
        raise ValueError("%s was not found in the config file"%(args.instrum))
    key = None
    if os.path.isfile(KEY_FILE):
        with open(KEY_FILE, "rb") as fil:
            key = fil.readline()
    if key is None or key == b'':
        # generate key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as fil:
            fil.write(key)
        os.chmod(KEY_FILE, 0o600)
    fern = Fernet(key)
    prompt = f"enter password for {args.instrum}:"
    sql_passwd = bytes(getpass.getpass(prompt=prompt, stream=sys.stderr), 'utf-8')
    sql_passwd = fern.encrypt(sql_passwd).decode('utf8')
    config.set(args.instrum, "sql_passwd", sql_passwd)
    overwrite(config)
