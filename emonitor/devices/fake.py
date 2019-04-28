# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import logging
from random import random, gauss
from .base import Device
logger = logging.getLogger(__name__)


class FakeError(ValueError):
    """ `DON'T PANIC`
    """
    pass


class Fake(Device):
    """ simulate comms. with a serial device"""
    tvals = [293, 299, 305, 306]

    def __init__(self, settings):
        self.settings = settings
        self.sensors = settings["sensors"]
        self.real_data = self.tvals

    def read_data(self, sensors=None):
        """ return fake sensor data """
        if sensors is None:
            sensors = self.sensors
        for i, sen in enumerate(sensors):
            logger.debug(f"read_data() sensor: {sen}")
            try:
                if random() < 0.05:
                    raise FakeError("DON'T PANIC")
                noise = gauss(0, 0.1)
                diff = self.tvals[i] - self.real_data[i]
                drift = gauss(0.5 * diff, 0.05)
                self.real_data[i] += drift
                value = self.real_data[i] + noise
                logger.debug(f"read_data() value: {value}")
                yield f"{value:.4f}"
            except:
                logger.exception("Exception occurred")
                yield None

    def close(self):
        pass
