# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 17:33:12 2019

@author: Adam
"""
import os
import logging
logger = logging.getLogger(__name__)

DIRE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(DIRE, "app/live.py")
HISTORY = os.path.join(DIRE, "app/history.py")

from bokeh.command.bootstrap import main

def plot(show=False, port=None):
    """ run Bokeh server
    """
    logging.info("emonitor plot")
    cmd = ["bokeh", "serve"]
    if show:
        cmd.append("--show")
    if port is not None:
        cmd.append("--port")
        cmd.append(str(port))
    cmd.append(LIVE) 
    cmd.append(HISTORY)
    main(cmd)