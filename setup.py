from setuptools import setup, find_packages
import os
import shutil
VERSION = '0.4.1'
MOD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.curdir))
EXAMPLE_INTRUM_FILE = os.path.join(MOD_PATH, 'instrum.ini')
USER_DIRE = os.path.join(os.path.expanduser("~"), '.emonitor')
USER_INSTRUM_FILE = os.path.join(USER_DIRE, 'instrum.ini')
DATA_DIRE = os.path.join(USER_DIRE, 'data')
TMP_DIRE = os.path.join(USER_DIRE, 'tmp')
LOG_DIRE = os.path.join(USER_DIRE, 'logs')

# create user instrum.ini
if not os.path.isdir(USER_DIRE):
    os.makedirs(USER_DIRE)
if not os.path.isdir(DATA_DIRE):
    os.makedirs(DATA_DIRE)
if not os.path.isdir(TMP_DIRE):
    os.makedirs(TMP_DIRE)
if not os.path.isdir(LOG_DIRE):
    os.makedirs(LOG_DIRE)
if not os.path.isfile(USER_INSTRUM_FILE):
    shutil.copy(EXAMPLE_INTRUM_FILE, USER_INSTRUM_FILE)

setup(name='emonitor',
      version=VERSION,
      description='record sensor data',
      url='',
      author='Adam Deller',
      license='BSD',
      packages = find_packages(),
      install_requires=['pyserial>=2.7', 'humanize', 'pymysql', 'bokeh>=2.0.0'],
      entry_points = {
        'console_scripts': ['emonitor=emonitor.emonitor:main'],
      },
      )
