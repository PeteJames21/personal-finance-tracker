"""
creates the application object as an instance of class Flask
imported from the flask package
"""
from flask import Flask, request, session
from flask_session import Session
from config import Config
from flask_login import LoginManager
from .models.engine.db_engine import DBEngine
from .models.user import User

app = Flask(__name__)
app.config.from_object(Config)
Session(app)
db = DBEngine()
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    user = db.get_user_by_username(user_id)
    return user


@app.before_request
def pre_request():
    db.reload()
    if start_date := request.args.get('startDate'):
        session['start_date'] = start_date
    if end_date := request.args.get('endDate'):
        session['end_date'] = end_date


from app import routes, models
