from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import Enum


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')
    reviews = db.relationship('Review')


class Dbteam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1 = db.Column(db.String(150),unique=True,nullable=False)
    team2 = db.Column(db.String(150),unique=True, nullable=False)
    day = db.Column(Enum('Lundi', 'Mardi', 'Mercredi', name='dayt_enum'), nullable=False)
    time = db.Column(Enum(
        '10:00', '11:00', '12:00', '13:00', '14:00', 
        '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', 
        name='timet_enum'
        ), nullable=False)

class Dbplayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1 = db.Column(db.String(150),unique=True,nullable=False)
    player2 = db.Column(db.String(150),unique=True, nullable=False)
    day = db.Column(Enum('Jeudi', 'Vendredi', name='dayp_enum'), nullable=False)
    time = db.Column(Enum(
        '10:00', '11:00', '12:00', '13:00', '14:00', 
        '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', 
        name='timep_enum'
        ), nullable=False)
    
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    user_id =db.Column(db.Integer, db.ForeignKey('user.id'))
