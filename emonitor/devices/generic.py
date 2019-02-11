# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import codecs
import re
import logging
from serial import SerialException, Serial
from .tools import get_serial_settings
from .base import Device
logger = logging.getLogger(__name__)


class Generic(Serial, Device):
    """ communication with a serial device """
    def __init__(self, settings):
        self.settings = settings
        self.serial_settings = get_serial_settings(settings)
        self.sensors = settings.get("sensors", None)
        self.cmd = codecs.decode(self.settings["cmd"], "unicode-escape")
        self.regex = settings.get("regex", None)
        if "null_values" in self.settings:
            self.null_values = self.settings["null_values"]
        else:
            self.null_values = None
        self.num_serial_errors = 0
        # initialise Serial class
        super().__init__(**self.serial_settings)

    def check_reset(self):
        """ check / reset connection """
        try:
            self.flush()
            if self.num_serial_errors > 0:
                logger.info("Reconnected to serial device")
                self.num_serial_errors = 0
        except:
            self.num_serial_errors += 1
            if self.num_serial_errors == 1:
                # log first failure
                logger.warning("Disconnected from serial device", exc_info=True)
            # attempt to reset
            if self.is_open:
                self.close()
            self.open()
            self.flush()

    def read_data(self, sensors=None):
        """ read sensor data """
        # check connection and flush buffer
        if sensors is None:
            sensors = self.sensors
        logger.debug(f"read_data() sensors: {sensors}")
        try:
            self.check_reset()
        except:
            # failed to open serial connection
            return
        # query instrument
        for sen in sensors:
            try:
                self.flushInput()
                # parse command
                serial_cmd = self.cmd.replace("{sensor}", sen)
                serial_cmd = bytes(serial_cmd, "utf8")
                logger.debug(f"read_data() sensor {sen} query: {serial_cmd}")
                # write command, read response
                self.write(serial_cmd)
                # wait for acknowledgement / send enquiry
                if "ack" in self.settings and "enq" in self.settings:
                    # needed for maxigauge
                    ack = codecs.decode(self.settings["ack"], "unicode-escape")
                    response = self.readline()
                    logger.debug(f"read_data() sensor {sen} acknowledgement: {response}")
                    if response == bytes(ack, "utf8"):
                        # send enquiry
                        enq = codecs.decode(self.settings["enq"], "unicode-escape")
                        self.write(bytes(enq, "utf8"))
                    else:
                        raise SerialException("sensor {sen} acknowledgement failed")
                response = self.readline()
                logger.debug(f"read_data() sensor {sen} response: {response}")
                # format response
                response = response.strip().decode("utf-8")
                if self.regex is not None:
                    match = re.search(self.regex, response)
                    response = match.group(1)
                    logger.debug(f"read_data() sensor {sen} regex `{self.regex}` match: {response}")
                # check if result is a known null value
                if self.null_values is not None and response in self.null_values:
                    response = None
                yield response
            except:
                logger.exception("Exception occurred")
                yield None
