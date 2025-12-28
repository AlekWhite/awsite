from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, datetime
import datetime as dt
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

    @classmethod
    def add_temp(cls, avg_temp, timestamp=None):
        new_reading = cls(
            avg_temp=avg_temp,
            timestamp=timestamp if timestamp else datetime.utcnow()
        )
        db.session.add(new_reading)
        db.session.commit()
        return new_reading
    
    @classmethod
    def get_all(cls):
        """Get all temperature readings (max 24 due to trigger)"""
        return cls.query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def cleanup_excess_entries(cls):
        """Manually trigger cleanup to maintain 24-entry limit"""
        subquery = cls.query.order_by(cls.timestamp.desc()).offset(24).subquery()
        deleted_count = cls.query.filter(cls.id.in_(db.session.query(subquery.c.id))).delete(synchronize_session=False)
        db.session.commit()
        return deleted_count

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
    def get_last_hour(cls):
        """Get all temperature readings from the last hour"""
        one_hour_ago = datetime.utcnow() - timedelta(minutes=dt.datetime.now().minute)
        return cls.query.filter(cls.timestamp >= one_hour_ago).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def add_temp(cls, temp, timestamp=None):
        """Add a single temperature reading"""
        new_temp = cls(
            current_temp=temp,
            timestamp=timestamp if timestamp else datetime.utcnow()
        )
        db.session.add(new_temp)
        db.session.commit()
        cls.cleanup_old_readings()
        return new_temp
    
    @classmethod
    def cleanup_old_readings(cls):
        """Delete all readings older than 1 hour"""
        one_hour_ago = datetime.utcnow() - timedelta(minutes=dt.datetime.now().minute)
        deleted_count = cls.query.filter(cls.timestamp < one_hour_ago).delete()
        db.session.commit()
        return deleted_count
    
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