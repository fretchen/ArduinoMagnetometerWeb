import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # ...
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'amTestKey'
    SERIAL_PORT = 'COM32'
    REMOTE_FILE = 'Test'
