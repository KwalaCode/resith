from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_team = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email1 = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    email2 = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    timeslot = db.Column(db.String(20), nullable=False)
    day = db.Column(db.Date, nullable=False)
    is_team_booking = db.Column(db.Boolean, default=False)

    @staticmethod
    def get_available_slots(date, is_team):
        day_name = date.strftime("%A")
        total_slots = 8 if day_name == "Friday" else 10
        booked_slots = Booking.query.filter_by(day=date).all()
        available_slots = [f"{h:02d}:00-{h+1:02d}:00" for h in range(10, 10+total_slots)]
        for booking in booked_slots:
            if booking.timeslot in available_slots:
                available_slots.remove(booking.timeslot)
        return available_slots

    @staticmethod
    def can_book(user_email):
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        existing_booking = Booking.query.filter(
            Booking.email1 == user_email,
            Booking.day >= start_of_week,
            Booking.day < start_of_week + timedelta(days=7)
        ).first()
        return existing_booking is None
    
    @staticmethod
    def get_available_slots(date, is_team):
        day_name = date.strftime("%A")
        total_slots = 8 if day_name == "Friday" else 10
        booked_slots = Booking.query.filter_by(day=date).all()
        available_slots = [f"{h:02d}:00-{h+1:02d}:00" for h in range(10, 10+total_slots)]
        for booking in booked_slots:
            if booking.timeslot in available_slots:
                available_slots.remove(booking.timeslot)
        return available_slots
    
class BookingForm(FlaskForm):
    opponent = SelectField('Adversaire', validators=[DataRequired()])
    timeslot = SelectField('Créneau horaire', validators=[DataRequired()])
    submit = SubmitField('Réserver')

class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User', backref=db.backref('admin_logs', lazy=True))

    def __repr__(self):
        return f'<AdminLog {self.admin_email}: {self.action}>'
