# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 19:10:53 2018

@author: Adam
"""
import os
from emonitor.core import INSTRUM_FILE

def test_instrum_exists():
    """ """
    assert os.path.exists(INSTRUM_FILE)