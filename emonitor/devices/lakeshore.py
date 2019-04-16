# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 12:38:01 2019

@author: Adam
"""
import codecs
import re
import logging
from .base import SerialDevice
logger = logging.getLogger(__name__)

DEFAULTS = {"parity" : "O", 
            "stopbits" : 1,
            "bytesize" : 7,
            "baudrate" : 57600,
            "timeout" : 1}


class Model_336(SerialDevice):
    """ read Lakeshore Model 336 temperature sensors """
    def __init__(self, settings):
        settings = {**DEFAULTS, **settings}
        self.set_units(settings.get("units", "K"))
        super().__init__(settings)
 
    def set_units(self, unit):
        """ update sensor units """
        assert unit in ["C", "K"]
        # update unit and command
        self.unit = unit
        self.cmd = codecs.decode(unit + "RDG?{sensor}\r\n", "unicode-escape")

    def read_sensor(self, sensor):
        """ read sensor data """
        # parse command
        serial_cmd = self.cmd.format(sensor=sensor)
        logger.debug(f"read_data() sensor={sensor} query: {serial_cmd}")
        # write command
        self.write(bytes(serial_cmd, "utf8"))
        # read response
        response = self.readline()
        logger.debug(f"read_data() sensor={sensor} response: {response}")
        # format
        response = response.strip().decode("utf-8")
        return response


class Model_331(Model_336):
    """ read Lakeshore Model 331 sensors """
    pass