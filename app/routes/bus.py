from flask import Blueprint, render_template

bus_bp = Blueprint('bus', __name__)

@bus_bp.route('/status')
def status():
    return render_template('bus_status.html')
