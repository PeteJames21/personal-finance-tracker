'''Stores configuration settings for the app
preferred value: environment variable else hardcoded string
'''
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    '''Stores configuration items'''
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sunday best'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

    # Flask_Session config options
    SESSION_USE_SIGNER = True
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
