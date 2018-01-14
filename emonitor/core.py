# -*- coding: utf-8 -*-
"""
Created on Mon Jan  1 21:38:13 2018

@author: Adam
"""
import os
import codecs
import re
from random import gauss
import serial

USER_DIRE = os.path.join(os.path.expanduser("~"), '.emonitor')
DATA_DIRE = os.path.join(USER_DIRE, 'data')
INSTRUM_FILE = os.path.join(USER_DIRE, 'instrum.ini')

class FakeInstrument(object):
    """ simulate comms. with a serial instrument"""
    def __init__(self, settings):
        self.config = settings
        self.sensors = (settings['sensors'].strip()).split(',')

    def read_all(self, debug=False, close=True):
        """ return fake sensor data """
        reads = []
        for i, sen in enumerate(self.sensors):
            reads.append('%.4f'%gauss(293 + 0.5*i, 0.1))
        return tuple(reads)

    def close(self):
        """ close connection"""
        pass

class Instrument(object):
    """ serial communication with an instrument"""
    def __init__(self, settings):
        self.settings = settings
        self.setup()
        self.sensors = (settings['sensors'].strip()).split(',')
        # format response
        if 'regex' in settings:
            self.regex = settings['regex']
        else:
            self.regex = None

    def setup(self):
        """ setup serial connection"""
        self.connection = serial.Serial()
        for att in ['port',
                    'baudrate',
                    'bytesize',
                    'parity',
                    'stopbits',
                    'timeout',
                    'xonxoff',
                    'rtsct',
                    'dsrdtr',
                    'write_timeout',
                    'inter_byte_timeout']:
            if att in self.settings:
                # check if int
                try:
                    val = int(self.settings[att])
                except ValueError:
                    val = self.settings[att]
                # update serial configuration
                setattr(self.connection, att, val)

    def read_all(self, debug=False, close=True):
        """ read sensor data"""
        # check connection and flush buffer
        try:
            if not self.connection.is_open:
                self.connection.open()
            self.connection.flush()
            # query instrument
            reads = []
            cmd = codecs.decode(self.settings['cmd'], 'unicode-escape')
            for sen in self.sensors:
                self.connection.flushInput()
                # parse command
                serial_cmd = cmd.replace('#', sen)
                serial_cmd = bytes(serial_cmd, 'utf8')
                if debug:
                    print(serial_cmd)
                # write command, read response
                self.connection.write(serial_cmd)
                # wait for acknowledgement / send enquiry
                if 'ack' in self.settings and 'enq' in self.settings:
                    # needed for maxigauge
                    ack = codecs.decode(self.settings['ack'], 'unicode-escape')
                    if self.connection.readline() == bytes(ack, 'utf8'):
                        # send enquiry
                        enq = codecs.decode(self.settings['enq'], 'unicode-escape')
                        self.connection.write(bytes(enq, 'utf8'))
                    else:
                        raise serial.SerialException('acknowledgement error')
                response = self.connection.readline()
                if debug:
                    print(response)
                # format response
                response = response.strip()
                response = response.decode("utf-8")
                if self.regex is not None:
                    match = re.search(self.regex, response)
                    response = match.group(1)
                reads.append(response)
            if close:
                # close connection
                self.connection.close()
            return tuple(reads)
        except serial.SerialException:
            print("Warning: serial connection failed.")
            return None

    def close(self):
        """ close connection"""
        if self.connection.is_open:
            self.connection.close()

