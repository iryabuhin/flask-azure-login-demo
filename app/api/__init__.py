from flask import Blueprint
from flask_cors import CORS

api = Blueprint('api', __name__)
# TODO is it better to enable CORS in a blueprint or in app/__init__.py with resources='/api/*' ?
CORS(api)

from . import errors, projects
