import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'correcthorsebatterystaple'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///../data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_ECHO shows SQL commands used to execute a query
    SQLALCHEMY_ECHO = False