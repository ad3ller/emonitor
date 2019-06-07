# -*- coding: utf-8 -*-
"""
Created on Fri May 07 17:12:11 2019

@author: Adam
"""
import codecs
import re
import logging
from .base import SerialDevice
logger = logging.getLogger(__name__)

CR = "\x0D"
LF = "\x0A"
ACK = "\x06"
ENQ = "\x05"
REGEX = "^0,(.*)"

DEFAULTS = {"parity" : "N", 
            "stopbits" : 1,
            "bytesize" : 8,
            "baudrate" : 9600,
            "timeout" : 1}


class MaxiGauge(SerialDevice):
    """ communication with a pfeiffer maxigauge """
    def __init__(self, settings):
        settings = {**DEFAULTS, **settings}
        self.cmd = codecs.decode("PR{sensor}" + CR + LF, "unicode-escape")
        self.regex = settings.get("regex", REGEX)
        super().__init__(settings)
 
    def read_sensor(self, sensor):
        """ read sensor data """
        # write command
        serial_cmd = self.cmd.format(sensor=sensor)
        logger.debug(f"read_sensor({sensor}), query: {serial_cmd}")
        self.write(bytes(serial_cmd, "utf8"))
        # wait for acknowledgement / send enquiry
        response = self.readline()
        logger.debug(f"read_sensor({sensor}), acknowledgement: {response}")
        if response == bytes(ACK + CR + LF, "utf8"):
            # send enquiry
            self.write(bytes(ENQ + CR + LF, "utf8"))
        else:
            raise Exception(f"read_sensor({sensor}) acknowledgement failed")
        # read response
        response = self.readline()
        logger.debug(f"read_sensor({sensor}), response: {response}")
        # format
        response = response.strip().decode("utf-8")
        match = re.search(self.regex, response)
        response = match.group(1)
        logger.debug(f"read_sensor({sensor}), regex match: {response}")
        return response
