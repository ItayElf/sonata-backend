import pathlib
import hashids
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

_DATABASE_LOCATION = pathlib.Path(__file__).parent.parent / "sonata.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_DATABASE_LOCATION}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

hasher = hashids.Hashids()
database = SQLAlchemy(app)
