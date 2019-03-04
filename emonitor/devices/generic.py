# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import codecs
import re
import logging
from serial import Serial
from .base import get_serial_settings, SerialDevice
logger = logging.getLogger(__name__)


class Generic(Serial, SerialDevice):
    """ communication with a serial device """
    def __init__(self, settings):
        self.settings = settings
        self.cmd = codecs.decode(settings["cmd"], "unicode-escape")
        self.regex = settings.get("regex", None)
        self.sensors = settings.get("sensors", None)
        self.null_values = settings.get("null_values", None)
        # initialise Serial class
        self.num_serial_errors = 0
        self.serial_settings = get_serial_settings(settings)
        super().__init__(**self.serial_settings)
 
    def read_sensor(self, sensor):
        """ read sensor data """
        # parse command
        serial_cmd = self.cmd.replace("{sensor}", sensor)
        serial_cmd = bytes(serial_cmd, "utf8")
        logger.debug(f"read_data() sensor {sensor} query: {serial_cmd}")
        # write command, read response
        self.write(serial_cmd)
        # wait for acknowledgement / send enquiry
        if "ack" in self.settings and "enq" in self.settings:
            # needed for maxigauge
            ack = codecs.decode(self.settings["ack"], "unicode-escape")
            response = self.readline()
            logger.debug(f"read_data() sensor {sensor} acknowledgement: {response}")
            if response == bytes(ack, "utf8"):
                # send enquiry
                enq = codecs.decode(self.settings["enq"], "unicode-escape")
                self.write(bytes(enq, "utf8"))
            else:
                raise Exception("sensor {sen} acknowledgement failed")
        response = self.readline()
        logger.debug(f"read_data() sensor {sensor} response: {response}")
        # format response
        response = response.strip().decode("utf-8")
        if self.regex is not None:
            match = re.search(self.regex, response)
            response = match.group(1)
            logger.debug(f"read_data() sensor {sensor} regex `{self.regex}` match: {response}")
        return response
