# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
from random import gauss
from .base import Device


class Fake(Device):
    """ simulate comms. with a serial device"""
    def __init__(self, settings):
        self.settings = settings
        self.sensors = settings["sensors"]

    def read_data(self, sensors=None, debug=False):
        """ return fake sensor data """
        if sensors is None:
            sensors = self.sensors
        data = []
        for i, _ in enumerate(sensors):
            data.append('%.4f'%gauss(293 + 0.5*i, 0.1))
        return tuple(data)

    def close(self):
        pass
