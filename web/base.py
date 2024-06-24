from datetime import timedelta
import os
import pathlib
from flask_jwt_extended import JWTManager
import hashids

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from web.hidden import SECRET, JWT_SECRET_KEY

_DATABASE_LOCATION = pathlib.Path(__file__).parent.parent / "sonata.db"

app = Flask(__name__)

app.config["SECRET"] = SECRET
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{
    os.environ.get('DATABASE_PATH', _DATABASE_LOCATION)}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

hasher = hashids.Hashids()
database = SQLAlchemy(app, session_options={"autoflush": False})
jwt = JWTManager(app)
