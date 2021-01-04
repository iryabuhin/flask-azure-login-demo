from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors, google_sheets, ictis_api, verify_form


