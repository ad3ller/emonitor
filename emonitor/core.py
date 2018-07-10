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
TABLE = 'data'
# special characters
CR = "\x0D"
LF = "\x0A"
ENQ = "\x05"
ACK = "\x06"

class FakeSerialInstrument(object):
    """ simulate comms. with a serial instrument"""
    def __init__(self, settings):
        self.config = settings
        self.sensors = [sen.strip() for sen in settings['sensors'].split(',')]

    def read_all(self, debug=False, close=True):
        """ return fake sensor data """
        reads = []
        for i in range(len(self.sensors)):
            reads.append('%.4f'%gauss(293 + 0.5*i, 0.1))
        return tuple(reads)

    def close(self):
        """ close connection"""
        pass

class SerialInstrument(object):
    """ serial communication with an instrument"""
    def __init__(self, settings):
        self.settings = settings
        self.setup()
        self.sensors = [sen.strip() for sen in settings['sensors'].split(',')]
        # format commands
        for tmp_key in ['cmd', 'ack', 'enq']:
            if tmp_key in self.settings:
                tmp_val = self.settings[tmp_key]
                # string placeholder replacements
                for placeholder, value in zip(["<CR>", "<LF>", "<ACK>", "<ENQ>"],
                                              [CR, LF, ACK, ENQ]):
                    if placeholder in tmp_val:
                        tmp_val = tmp_val.replace(placeholder, value)
                self.settings[tmp_key] = tmp_val
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
                    # check if float
                    try:
                        val = float(self.settings[att])
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
                serial_cmd = cmd.replace('<sensor>', sen)
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
