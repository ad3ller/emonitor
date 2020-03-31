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


class Temperature(Device):
    """ simulate comms. with a serial device"""
    tvals = {'A': 293, 'B': 299, 'C': 305, 'D': 306}

    def __init__(self, settings):
        self.settings = settings
        self.sensors = settings["sensors"]
        self.real_data = self.tvals

    def read_data(self, sensors=None):
        """ return fake sensor data """
        if sensors is None:
            sensors = self.sensors
        for sen in sensors:
            logger.debug(f"read_data() sensor: {sen}")
            try:
                if random() < 0.05:
                    raise FakeError("DON'T PANIC")
                noise = gauss(0.0, 0.1)
                diff = self.tvals[sen] - self.real_data[sen]
                drift = gauss(diff, 0.05)
                self.real_data[sen] += drift
                value = self.real_data[sen] + noise
                logger.debug(f"read_data() value: {value}")
                yield f"{value:.4f}"
            except:
                logger.exception("Exception occurred")
                yield None

    def close(self):
        pass


class Fake(Temperature):
    # legacy
    pass


class Pressure(Device):
    """ simulate comms. with a serial device"""
    pvals = {'1': 3e-6, '2': 1e-7, '3': 2e-9, '4': 3e-9, '5': 3e-2, '6':1.4e-2}

    def __init__(self, settings):
        self.settings = settings
        self.sensors = settings["sensors"]
        self.real_data = self.pvals

    def read_data(self, sensors=None):
        """ return fake sensor data """
        if sensors is None:
            sensors = self.sensors
        for sen in sensors:
            logger.debug(f"read_data() sensor: {sen}")
            try:
                if random() < 0.005:
                    raise FakeError("DON'T PANIC")
                value = self.real_data[sen] * gauss(1.0, 0.02)
                diff = self.pvals[sen] - value
                value += random()**2.0 * diff
                self.real_data[sen] = value
                logger.debug(f"read_data() value: {value}")
                yield f"{value:.4e}"
            except:
                logger.exception("Exception occurred")
                yield None

    def close(self):
        pass
