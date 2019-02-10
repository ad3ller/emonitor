# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import logging
from random import random, gauss
from .base import Device
logger = logging.getLogger(__name__)


class Fake(Device):
    """ simulate comms. with a serial device"""
    def __init__(self, settings):
        self.settings = settings
        self.sensors = settings["sensors"]

    def read_data(self, sensors=None):
        """ return fake sensor data """
        if sensors is None:
            sensors = self.sensors
        for i, sen in enumerate(sensors):
            logger.debug(f"read_data() sensor: {sen}")
            try:
                if random() < 0.05:
                    raise Exception("Fake error")
                value = gauss(293 + 0.5*i, 0.1)
                logger.debug(f"read_data() value: {value}")
                yield f"{value:.4f}"
            except:
                logger.exception("Exception occurred")
                yield None

    def close(self):
        pass
