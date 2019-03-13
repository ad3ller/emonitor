# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import logging
from abc import ABC, abstractmethod
from serial import Serial
logger = logging.getLogger(__name__)


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


class Device(ABC):
    """ emonitor device base class
    """
    @abstractmethod
    def read_data(self, sensors=None):
        pass

    @abstractmethod
    def close(self):
        pass


class SerialDevice(Serial, Device):
    """ communication with a serial device """
    def __init__(self, settings):
        self.sensors = settings.get("sensors", None)
        self.null_values = settings.get("null_values", None)
        # initialise Serial class
        self.num_serial_errors = 0
        super().__init__(**get_serial_settings(settings))

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
        """ read all sensor data """
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
        for sensor in sensors:
            try:
                self.flushInput()
                response = self.read_sensor(sensor)
                # check if result is a known null value
                if self.null_values is not None and response in self.null_values:
                    response = None
                yield response
            except:
                logger.exception("Exception occurred")
                yield None

    @abstractmethod
    def read_sensor(self, sensor):
        pass
