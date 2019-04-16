# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import codecs
import re
import logging
from .base import SerialDevice
logger = logging.getLogger(__name__)


class Generic(SerialDevice):
    """ communication with a serial device """
    def __init__(self, settings):
        self.cmd = codecs.decode(settings["cmd"], "unicode-escape")
        # acknowledge / enquire
        if "ack" in settings and "enq" in settings:
            self.ack = codecs.decode(settings["ack"], "unicode-escape")
            self.enq = codecs.decode(settings["enq"], "unicode-escape")
        else:
            self.ack = None
            self.enq = None
        # format response
        self.regex = settings.get("regex", None)
        super().__init__(settings)
 
    def read_sensor(self, sensor):
        """ read sensor data """
        # parse command
        serial_cmd = self.cmd.format(sensor=sensor)
        logger.debug(f"read_data() sensor={sensor} query: {serial_cmd}")
        # write command
        self.write(bytes(serial_cmd, "utf8"))
        # wait for acknowledgement / send enquiry
        if self.ack is not None and self.enq is not None:
            response = self.readline()
            logger.debug(f"read_data() sensor={sensor} acknowledgement: {response}")
            if response == bytes(self.ack, "utf8"):
                # send enquiry
                self.write(bytes(self.enq, "utf8"))
            else:
                raise Exception(f"sensor={sensor} acknowledgement failed")
        # read response
        response = self.readline()
        logger.debug(f"read_data() sensor={sensor} response: {response}")
        # format response
        response = response.strip().decode("utf-8")
        if self.regex is not None:
            match = re.search(self.regex, response)
            response = match.group(1)
            logger.debug(f"read_data() sensor={sensor} regex `{self.regex}` match: {response}")
        return response
