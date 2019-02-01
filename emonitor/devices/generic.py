# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import codecs
import re
import warnings
from serial import SerialException, Serial
from .tools import get_serial_settings
from .base import Device


class Generic(Serial, Device):
    """ communication with a generic serial device """
    def __init__(self, settings, debug=False):
        self.settings = settings
        self.serial_settings = get_serial_settings(settings)
        self.sensors = settings.get("sensors", None)
        self.regex = settings.get("regex", None)
        # initialise Serial class
        if debug:
            print("serial settings:", self.serial_settings)
        super().__init__(**self.serial_settings)

    def read_data(self, sensors=None, debug=False):
        """ read sensor data"""
        # check connection and flush buffer
        if sensors is None:
            sensors = self.sensors
        if debug:
            print("sensors:", sensors)
        try:
            if not self.is_open:
                self.open()
            self.flush()
            # query instrument
            data = []
            cmd = codecs.decode(self.settings['cmd'], 'unicode-escape')
            for sen in sensors:
                self.flushInput()
                # parse command
                serial_cmd = cmd.replace("{sensor}", sen)
                serial_cmd = bytes(serial_cmd, 'utf8')
                if debug:
                    print("serial cmd:", serial_cmd)
                # write command, read response
                self.write(serial_cmd)
                # wait for acknowledgement / send enquiry
                if 'ack' in self.settings and 'enq' in self.settings:
                    # needed for maxigauge
                    ack = codecs.decode(self.settings['ack'], 'unicode-escape')
                    response = self.readline()
                    if debug:
                        print("acknowledgement:", response, bytes(ack, 'utf8'))
                    if response == bytes(ack, 'utf8'):
                        # send enquiry
                        enq = codecs.decode(self.settings['enq'], 'unicode-escape')
                        self.write(bytes(enq, 'utf8'))
                    else:
                        raise SerialException('Acknowledgement failed')
                response = self.readline()
                if debug:
                    print(response)
                # format response
                response = response.strip().decode("utf-8")
                if self.regex is not None:
                    match = re.search(self.regex, response)
                    response = match.group(1)
                data.append(response)
            return tuple(data)
        except (SerialException, AttributeError, AssertionError) as error:
            warnings.warn(error)
            return None
