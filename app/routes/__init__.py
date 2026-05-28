from flask import Blueprint

main_bp = Blueprint('main', __name__)
bus_bp = Blueprint('bus', __name__)
driver_bp = Blueprint('driver', __name__)

from . import main, bus, driver
