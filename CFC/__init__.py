import secrets

from flask import Flask
from datetime import timedelta

from .views.students import student, login_manager

from .models import Base, engine


# Web App Settings
cfc = Flask(__name__)
cfc.permanent_session_lifetime = timedelta(minutes=10)
cfc.secret_key = secrets.token_urlsafe(32)

# registering student route (sub route)
cfc.register_blueprint(student)
login_manager.init_app(cfc)

# Create database tables
try: Base.metadata.create_all(engine)
except Exception as E: print(f'\nError creating database\nError" {E}')