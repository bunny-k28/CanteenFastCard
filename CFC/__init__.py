import secrets

from flask import Flask
from datetime import timedelta

from .views.students import student
from .views.admin import admin

from .models import Base, engine


# Web App Settings
cfc = Flask(__name__)
cfc.permanent_session_lifetime = timedelta(minutes=10)
cfc.secret_key = secrets.token_urlsafe(32)

# registering the blueprints (sub routes)
cfc.register_blueprint(admin)
cfc.register_blueprint(student)


# Create database tables
try: Base.metadata.create_all(engine)
except Exception as E: print(f'\nError creating database\nError" {E}')