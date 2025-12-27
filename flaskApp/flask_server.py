from flask import Flask, request, session, render_template, redirect, url_for
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import select, update
from flask import app as application
from datetime import timedelta
from dotenv import load_dotenv
from threading import Thread
import secrets
import time
import json
import os

from model import User, Arduino, FishOfTheWeek, TemperatureData, RGBLightValue, CurrentTemperature, db 

# pull info from .env
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# server setup
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.static_folder = 'static'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True 
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db.init_app(app)
csrf = CSRFProtect(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# deliver main html page
@app.route('/', methods=['GET'])
def main_page():
    return render_template("mainPage.html")

# login for the web-app clients 
@app.route('/auth_page', methods=['GET', 'POST'])
@limiter.limit("15 per minute")
def auth_page():
    if request.method == 'GET':
        return render_template("authPage.html")

    un = request.form.get("Username").strip()
    pw = request.form.get("Password").strip()
    if not un or not pw or len(un) > 100 or len(pw) > 100:
        time.sleep(.5)
        return json.dumps({"error": "Invalid credentials"}), 401
    print(request.form)
    user = User.query.filter_by(username=un).first()

    if not user or not check_password_hash(user.password_hash, pw):
        time.sleep(.5)
        return json.dumps({"error": "Invalid credentials"}), 401
    session.clear()
    session.permanent = True
    session['user_id'] = user.id
    return redirect(url_for("dashboard"))

# private dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))

    if request.method == 'POST':

        # update light colors in the db
        data = request.form.get("light")
        if data and (Arduino.get_state != "update"):
            try:
                light_data = json.loads(data)
            except json.JSONDecodeError:
                time.sleep(1)
                return "Invalid JSON format", 400
            print(light_data)
            if light_data['zone'] == "all-on":
                RGBLightValue.get_by_name("zone1").update_color(255, 0, 0)
                RGBLightValue.get_by_name("zone2").update_color(55, 0, 200)
            elif light_data['zone'] == "all-off":
                RGBLightValue.get_by_name("zone1").update_color(0, 0, 0)
                RGBLightValue.get_by_name("zone2").update_color(0, 0, 0)
            else:
                RGBLightValue.get_by_name(light_data['zone']).update_color(light_data['r'], light_data['g'], light_data['b'])
            Arduino.update_state("update")
            time.sleep(0.15)

    return render_template("dashboard.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main_page'))

@app.route('/api/arduino', methods=['GET'])
@limiter.limit("10 per minute", methods=["GET"])
def arduino():
    if 'user_id' not in session:
        return json.dumps({"error": "Invalid credentials"}), 401
    ard_out = {
        "status": Arduino.get_state(),
        "port": Arduino.get_port()}
    return json.dumps(ard_out), 200
   