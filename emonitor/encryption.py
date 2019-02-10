# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import os
import logging
from cryptography.fernet import Fernet
logger = logging.getLogger(__name__)


def fernet_key(key_file):
    """ read or generate key file
    """
    key = None
    if os.path.isfile(key_file):
        # read existing key
        with open(key_file, "rb") as fil:
            key = fil.readline()
    if key is None or key == b'':
        # generate new key
        logger.info(f"fernet_key(): generate new key {key_file}")
        key = Fernet.generate_key()
        with open(key_file, "wb") as fil:
            fil.write(key)
        os.chmod(key_file, 0o600)
    return Fernet(key)
