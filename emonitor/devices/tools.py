# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 11:41:13 2018

@author: Adam
"""


def get_serial_settings(settings):
    """ extract serial settings
    """
    serial_keys = ["port",
                   "baudrate",
                   "bytesize",
                   "parity",
                   "stopbits",
                   "timeout",
                   "xonxoff",
                   "rtscts",
                   "write_timeout",
                   "dsrdtr",
                   "inter_byte_timeout",
                   "exclusive"]
    serial_settings = {k: settings[k] for k in settings.keys() & serial_keys}
    return serial_settings
