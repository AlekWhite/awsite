from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

class TemperatureData(db.Model):
    __tablename__ = 'temperature_data'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    avg_temp = db.Column(db.Float, nullable=False)

class CurrentTemperature(db.Model):
    __tablename__ = 'current_temperature'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_temp = db.Column(db.Float, nullable=False)

    @classmethod
    def get_current(cls):
        """Get the current temperature reading"""
        return cls.query.order_by(cls.timestamp.desc()).first()
    
    @classmethod
    def update_temp(cls, temp):
        """Update current temperature (replaces existing)"""
        # Delete all existing readings
        cls.query.delete()
        # Insert new reading
        new_temp = cls(current_temp=temp)
        db.session.add(new_temp)
        db.session.commit()
        return new_temp
    
class RGBLightValue(db.Model):
    __tablename__ = 'rgb_light_vals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    red = db.Column(db.Integer, nullable=False)
    green = db.Column(db.Integer, nullable=False)
    blue = db.Column(db.Integer, nullable=False)

    @property
    def rgb_tuple(self):
        """Returns RGB values as a tuple"""
        return (self.red, self.green, self.blue)
        
    @classmethod
    def get_by_name(cls, zone_name):
        """Get RGB values for a specific zone"""
        return cls.query.filter_by(name=zone_name).first()
    
    def update_color(self, red, green, blue):
        """Update the RGB values for this zone"""
        self.red = red
        self.green = green
        self.blue = blue
        db.session.commit()

class FishOfTheWeek(db.Model):
    __tablename__ = 'fish_of_the_week'
    id = db.Column(db.Integer, primary_key=True)
    wiki_url = db.Column(db.String(500), unique=True, nullable=False)
    fish_name = db.Column(db.String(200), nullable=False)
    last_chosen_week = db.Column(db.Date, nullable=True)
    
    @classmethod
    def get_random_fish(cls):
        """Get a random fish that hasn't been chosen recently"""
        # Find fish not chosen in last 12 weeks, or never chosen
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        cutoff_date = monday - timedelta(weeks=12)
        fish = cls.query.filter(
            (cls.last_chosen_week == None) | (cls.last_chosen_week < cutoff_date)
        ).order_by(func.random()).first()
        return fish
    
    def mark_as_chosen(self):
        """Mark this fish as chosen for current week"""
        from datetime import date, timedelta
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        self.last_chosen_week = monday
        db.session.commit()

class Arduino(db.Model):
    __tablename__ = 'arduino'
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(20), nullable=False)

    @classmethod
    def get_state(cls):
        """Get the current Arduino state"""
        return cls.query.first().state

    @classmethod
    def get_port(cls):
        """Get the current Arduino port"""
        return cls.query.first().port
    
    @classmethod
    def update_state(cls, new_state):
        """Update Arduino state"""
        arduino = cls.query.first()
        if arduino:
            arduino.state = new_state
        db.session.commit()
        return arduino

    @classmethod
    def update_port(cls, port):
        """Update Arduino port"""
        arduino = cls.query.first()
        if arduino:
            arduino.port = port
        db.session.commit()
        return arduino