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
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
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
    if 'user_id' in session:
        session.pop('user_id', None)
    print(session)
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
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))

    if request.method == 'POST':

        # update ard port in db
        np = request.form.get("newPort")
        if np and (len(np) < 100):
            print(np)
            Arduino.update_state("update")
            Arduino.update_port(np)

    return render_template("dashboard.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main_page'))

@app.route('/api/arduino', methods=['GET'])
def arduino():
    if 'user_id' not in session:
        return json.dumps({"error": "Invalid credentials"}), 401
    ard_out = {
        "status": Arduino.get_state(),
        "port": Arduino.get_port()}
    return json.dumps(ard_out), 200
   