from flask import Flask, request, render_template, jsonify, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask import send_from_directory
from flask_limiter import Limiter
from dotenv import load_dotenv
from datetime import timedelta
import random
import os
import re

from model import Arduino, FishOfTheWeek, GameUser, db

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
app.config['CACHE_TYPE'] = 'simple' 
app.config['CACHE_DEFAULT_TIMEOUT'] = 604800 

# edit fish update interval here 
#import pytz
#from datetime import datetime
#est = pytz.timezone("America/New_York")
#now = datetime.now(est)
#target = now + timedelta(minutes=2)
#app.fish_interval = {"day_of_week": target.strftime("%a").lower(), "hour": target.hour, "minute": target.minute, "second": target.second}

app.fish_interval = {"day_of_week": 'fri', "hour": 23, "minute": 59, "second": 59}
print(f"FISH INTERVAL: {app.fish_interval}")

db.init_app(app)
csrf = CSRFProtect(app)
with app.app_context():
    Arduino.initialize_cache()

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


""" <--------------- ICO/IMAGE FILES ---------------> """


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# serve public fish images
@app.route('/fish/<filename>')
@limiter.limit("100 per minute")
def serve_public_fish(filename):
    public_dir = os.path.join(app.static_folder, 'fish', 'public')
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        abort(404)
    file_path = os.path.join(public_dir, filename)
    if not os.path.exists(file_path):
        abort(404)  
    response = send_from_directory(public_dir, filename)
    response.headers['Cache-Control'] = 'public, max-age=604800'
    response.headers['Vary'] = 'Accept-Encoding'
    return response


""" <--------------- PAGES ---------------> """


# deliver main html page
@app.route('/', methods=['GET'])
@limiter.limit("15 per minute")
def main_page():
    return render_template("mainPage.html")

# deliver guess_the_fish page
@app.route('/guess_the_fish', methods=['GET'])
@limiter.limit("15 per minute")
def game_page():
    user_id = request.cookies.get('guestToken')
    user = GameUser.get_by_id(user_id)
    if not user:
        return render_template("mainPage.html")
    return render_template("guess_the_fish.html")

# deliver main html page
@app.route('/leaderboard', methods=['GET'])
@limiter.limit("15 per minute")
def lb_page():
    return render_template("leaderboard.html")

# admin page
@app.route('/admin_page', methods=['GET'])
@limiter.limit("15 per minute")
def admin_page():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_page'))
    return render_template("admin.html")

""" <--------------- FISH API ---------------> """


# gets previous fish from the db
@app.route('/api/fish', methods=['GET'])
@limiter.limit("60 per minute")
def get_old_fish():
    fish_list = FishOfTheWeek.get_fish()
    if fish_list:
        fish_list.pop(0)
    out = [{
            'name': fish.fish_name,
            'wiki_url': fish.wiki_url,
            'date': fish.last_chosen_week}
        for fish in fish_list]
    return jsonify({'fish': out, 'fish_interval':app.fish_interval}), 200

# gets time until next fish
@app.route('/api/time', methods=['GET'])
@limiter.limit("60 per minute")
def get_fish_time():
    return jsonify({'fish_interval':app.fish_interval}), 200

# gets current fish from the db
@app.route('/api/the_fish', methods=['GET'])
@limiter.limit("60 per minute")
def get_the_fish():

    user_id = request.cookies.get('guestToken')
    user = GameUser.get_by_id(user_id)
    if not user:
        return render_template("mainPage.html")
    elif user.final_score >= 0:
        user.update(is_leaderboard_eligible=False)

    fish_list = FishOfTheWeek.get_fish()
    out = {}
    if fish_list:
        fish = fish_list[0]
        out = {
            'name': fish.fish_name,
            'wiki_url': fish.wiki_url,
            'date': fish.last_chosen_week}
    return jsonify({'fish': out, 'fish_interval':app.fish_interval}), 200

# gets leaderboard
@app.route('/api/leaderboard', methods=['GET'])
@limiter.limit("60 per minute")
def get_leaderboard():
    return jsonify([{
        column.name: getattr(user, column.name)
        for column in user.__table__.columns}
    for user in GameUser.get_leaderboard()])

@app.route('/api/guess', methods=['POST'])
@limiter.limit("15 per minute")
@csrf.exempt
def guess():
     if request.method == 'POST':

        # get user
        user_id = request.cookies.get('guestToken')
        user = GameUser.get_by_id(user_id)
        if not user:
            return render_template("mainPage.html")
        
        # get fish
        fish_list = FishOfTheWeek.get_fish()
        fish_name = ""
        if fish_list:
            fish_name = fish_list[0].fish_name.strip().lower()
        if not fish_name:
            return "", "500 No fish found :("

        # get guess
        data = request.get_json()
        guess_in = data.get("guess")
        guess = re.findall(r"^[a-z ]+$", guess_in)
        if guess:
            guess = guess[0]
        if len(guess) > len(fish_name):
            return "", f"400 The length of your guess cannot exceed {len(fish_name)} characters"
        
        # get game vars
        ks = user.known_string
        yl = user.yellows.replace(" ", "")
        fa = user.fails.replace(" ", "")
        ap = user.final_score

        # check if reset is needed
        if (str(user.guess_date)[:10] != str(fish_list[0].last_chosen_week)) or (len(ks) != len(fish_name)):
            user.update(guess_date=fish_list[0].last_chosen_week)
            guess = []
            ks = ""
            yl = ""
            fa = ""
            ap = 0

        # dont allow guesses after winning
        if user.final_score < 0:
            out = user.to_dict()
            out["yellows"] = out["yellows"].replace(" ", "")
            out["fails"] = out["fails"].replace(" ", "")
            return jsonify(out), 200

        # do empty guess
        if guess == []:
            if ks == "":
                for c in fish_name:
                    if c == " ":
                        ks += " "
                    else:
                        ks += "_"

        # do single letter guesses 
        if len(guess) == 1:
            ap += 1000000
            if guess not in fish_name:
                if guess not in fa:
                    fa += guess
            else:
                new_ks = ""
                for i in range(len(fish_name)):
                    if fish_name[i] == guess:
                        new_ks += guess
                    else:
                        new_ks += ks[i]
                ks = new_ks
            
        # do phrase guesses
        if len(guess) > 1:
            ap += 1
            new_guess = ""
            for i in range(len(guess)):
                if guess[i] not in fish_name:
                    if guess[i] not in fa:
                        fa += guess[i]
                    new_guess += "_"
                else:
                    new_guess += guess[i]
 
            new_ks = ""
            for i in range(len(new_guess)):
                if new_guess[i] == "_":
                    new_ks += ks[i]
                    continue
                if new_guess[i] == fish_name[i]:
                    new_ks += new_guess[i]
                elif new_guess[i] not in yl:
                    yl += new_guess[i]
                    new_ks += ks[i]
                else:
                    new_ks += ks[i]

            offset = len(new_ks)
            for i in range(len(ks)-offset):
                new_ks += ks[i+offset]
            ks = new_ks
                
        # if win, get final score
        if ks == fish_name:
            total_points = 10000
            letter_pen = total_points / (-2*len(fish_name))
            phrase_pen = letter_pen / 2
            ap = -1*(total_points + int(phrase_pen*((ap % 1000000)-1)) + int(letter_pen*int(ap/1000000)))
            if ap > 0:
                ap = -1  

        # save & return new data
        user.update(known_string=ks, yellows=yl, fails=fa, final_score=ap)
        out = user.to_dict()
        out["known_string"] = ks
        out["yellows"] = yl
        out["fails"] = fa
        out["final_score"] = ap
        return jsonify(out), 200


""" <--------------- USER API ---------------> """


# make an new user in the db
@app.route('/api/make_user', methods=["GET"])
@limiter.limit("10 per hour")
@csrf.exempt
def make_user():
    user_id = request.cookies.get('guestToken')
    user = GameUser.get_by_id(user_id)
    if not user:
        name = "Guest-" + str(random.randint(1,999999)).rjust(6, '0')
        user = GameUser.create(name=name, known_string="")
        response = jsonify({'status': 'ok', 'name': user.name})
        response.set_cookie(
            'guestToken',
            user.id,
            httponly=True,
            samesite='Lax',
            secure=True,
            max_age=60 * 60 * 24 * 365 * 2
        )
        return response
    return jsonify({'status': 'ok', 'name': user.name})

# get all user data
@app.route('/api/user', methods=['GET'])
@limiter.limit("15 per minute")
@csrf.exempt
def user_data():
    user_id = request.cookies.get('guestToken')
    user = GameUser.get_by_id(user_id)
    if not user:
        return "", "403 no user in cookie"
    return jsonify(user.to_dict()), 200

# set new username
@app.route('/api/new_user_name', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
def new_user_name():
    user_id = request.cookies.get('guestToken')
    user = GameUser.get_by_id(user_id)

    if not user:
        return render_template("mainPage.html")
    data = request.get_json()
    new_name = data.get("new_name")

    if len(new_name) > 100:
        return jsonify({'error': True}), "400 Name cannot exceed 100 characters"

    if re.search(r"^[a-z0-9]+$", new_name):
        user.update(name=new_name)
        return jsonify({'status': 'ok', 'name': user.name})
    
    return jsonify({'error':  True}), "400 Name can only have characters [a-z] and [0-9]"

""" <--------------- ADMIN ---------------> """

from flask import redirect, url_for, make_response
from werkzeug.security import check_password_hash
from itsdangerous import URLSafeTimedSerializer
from model import User
import json

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# login for the web-app clients 
@app.route('/auth_page', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def auth_page():
    print(request.method)
    if request.method == 'GET':
        user = get_current_user()
        if not user:
            return render_template("authPage.html")
        return redirect(url_for('admin_page'))


    un = request.form.get("Username").strip()
    pw = request.form.get("Password").strip()
    if not un or not pw or len(un) > 100 or len(pw) > 100:
        return json.dumps({"error": "Invalid credentials"}), 401
    user = User.query.filter_by(username=un).first()

    if not user or not check_password_hash(user.password_hash, pw):
        return json.dumps({"error": "Invalid credentials"}), 401
    
    response = make_response(redirect(url_for('admin_page')))
    token = serializer.dumps(user.id, salt='auth-cookie')
    response.set_cookie(
        'authToken',
        token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=60 * 60 
    )
    return response

# logout
@app.route('/logout', methods=['POST'])
@limiter.limit("10 per minute")
def logout():
    response = redirect(url_for('main_page'))
    response.delete_cookie('authToken', httponly=True, samesite='Lax', secure=True)
    return response

def get_current_user():
    token = request.cookies.get('authToken')
    if not token:
        return None
    try:
        user_id = serializer.loads(token, salt='auth-cookie', max_age=3600)
        return User.query.get(user_id)
    except Exception:
        return None
    
@app.route('/api/admin/records', methods=['GET'])
@limiter.limit("15 per minute")
def admin_records():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_page'))
    page = request.args.get('p', default=0, type=int)
    per_page = 50
    records = (GameUser.query
               .order_by(GameUser.guess_date.desc())
               .offset(page * per_page)
               .limit(per_page)
               .all())
    return jsonify({
        'page': page,
        'per_page': per_page,
        'records': [r.to_dict() for r in records]
    })

@app.route('/api/admin/update', methods=['POST'])
@limiter.limit("60 per minute")
def admin_update():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_page'))
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'error': 'Missing id'}), 400
    record = GameUser.get_by_id(data['id'])
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    allowed = {'name', 'known_string', 'yellows', 'fails',
               'final_score', 'is_leaderboard_eligible', 'guess_date'}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400
    record.update(**updates)
    return jsonify({'status': 'ok', 'record': record.to_dict()})

@app.route('/api/admin/delete', methods=['POST'])
@limiter.limit("60 per minute")
def admin_delete():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_page'))
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'error': 'Missing id'}), 400
    success = GameUser.delete_by_id(data['id'])
    if not success:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify({
        'status': 'ok',
        'deleted_id': data['id']
    })
     
""" <--------------- OLD THINGS ---------------> """

"""
from model import User, TemperatureData, RGBLightValue,  CurrentTemperature
from werkzeug.security import check_password_hash
from flask import redirect, url_for, session
from datetime import datetime
import pytz
import json

# private dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    if request.method == 'POST':

        # update light colors in the db
        data = request.form.get("light")
        if data and (Arduino.get_state() != "update"):

            # get and validate form input 
            try:
                light_data = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"json-error: {e}")
                return "Invalid JSON format", 400
            print(light_data)

            # update the db with new colors
            if light_data['zone'] == "all-on":
                RGBLightValue.get_by_name("zone1").update_color(255, 0, 0)
                RGBLightValue.get_by_name("zone2").update_color(55, 0, 200)
            elif light_data['zone'] == "all-off":
                RGBLightValue.get_by_name("zone1").update_color(0, 0, 0)
                RGBLightValue.get_by_name("zone2").update_color(0, 0, 0)
            else:
                RGBLightValue.get_by_name(light_data['zone']).update_color(light_data['r'], light_data['g'], light_data['b'])
            Arduino.update_state("update")

    # get selected colors from the db
    colors = {}
    zones = ["zone1", "zone2"]
    rgb_button_map = {(0, 0, 0): "off", (255, 0, 0): "red", (0, 255, 0): "green", (0, 0, 255): "blue", (55, 0, 200): "purple"}
    for z in zones:
        rgb =  RGBLightValue.get_by_name(z).rgb_tuple
        if rgb in rgb_button_map:
            colors[z] = rgb_button_map[rgb]
        else:
            colors[z] = "none"
    print(colors)

    return render_template("dashboard.html", colorData=colors)

# logout a user
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main_page'))

# gets arduino status from the db 
@app.route('/api/arduino', methods=['POST'])
@limiter.limit("30 per minute")
def arduino():
    if 'user_id' not in session:
        return json.dumps({"error": "Invalid credentials"}), 401
    ard_out = {
        "status": Arduino.get_state(),
        "port": Arduino.get_port()}
    return json.dumps(ard_out), 200
   
# gets temperature data from the db
@app.route('/api/temperature', methods=['POST'])
@limiter.limit("30 per minute")
def temperature():
    if 'user_id' not in session:
        return json.dumps({"error": "Invalid credentials"}), 401
    
    db_data = TemperatureData.get_all()
    est = pytz.timezone('America/New_York')
    chart_data = None
    if db_data and (len(db_data) > 0):
        chart_data = {
            'cols': [
                {'label': 'Time', 'type': 'string'},
                {'label': 'Temperature (°F)', 'type': 'number'}],
            'rows': [
                {'c': [{'v': t.timestamp.replace(tzinfo=pytz.utc).astimezone(est).strftime('%I:%M %p')},
                       {'v': float(int((((t.avg_temp*(9/5))+32))*10))/10}]} for t in reversed(db_data)]}
        
    ct_val = CurrentTemperature.get_current()
    ct_out = None
    if ct_val:
        ct_out = round((ct_val.current_temp * (9/5) + 32), 1)

    out = {"chartData": chart_data, "ct": ct_out}
    return jsonify(out), 200
"""