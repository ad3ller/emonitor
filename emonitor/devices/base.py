# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
from abc import ABC, abstractmethod


class Device(ABC):
    """ emonitor device base class
    """
    @abstractmethod
    def read_data(self, sensors=None, debug=False):
        pass

    @abstractmethod
    def close(self):
        pass
