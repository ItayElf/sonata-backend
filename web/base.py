from datetime import timedelta
import os
import pathlib
from flask_jwt_extended import JWTManager
import hashids

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

from web.hidden import SECRET, JWT_SECRET_KEY

_DATABASE_LOCATION = pathlib.Path(__file__).parent.parent / "sonata.db"
_STATIC_FOLDER = pathlib.Path(__file__).parent.parent / "website"

app = Flask(__name__, static_folder=str(_STATIC_FOLDER), static_url_path="/")

app.config["SECRET"] = SECRET
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{
    os.environ.get('DATABASE_PATH', _DATABASE_LOCATION)}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config['CACHE_TYPE'] = 'simple'

cache = Cache(app)
hasher = hashids.Hashids()
database = SQLAlchemy(app, session_options={"autoflush": False})
jwt = JWTManager(app)


@app.route("/", defaults={'path': ''})
@app.route("/<path:path>")
def serve(path):
    print(repr(path), app.static_url_path, app.static_folder)
    # if path and os.path.exists(os.path.join(app.static_folder, path)):
    # return send_from_directory(app.static_folder, path)

    return send_from_directory(app.static_folder, "index.html")
