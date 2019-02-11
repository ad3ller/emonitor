# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import os

USER_DIRE = os.path.join(os.path.expanduser("~"), '.emonitor')
DATA_DIRE = os.path.join(USER_DIRE, 'data')
LOG_DIRE = os.path.join(USER_DIRE, 'logs')
INSTRUM_FILE = os.path.join(USER_DIRE, 'instrum.ini')
KEY_FILE = os.path.join(USER_DIRE, 'private.key')
TABLE = 'data'
