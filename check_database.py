import os
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models import User, Booking

app = create_app()

with app.app_context():
    print("Users in the database:")
    users = User.query.all()
    for user in users:
        print(f"- Email: {user.email}, Is Team: {user.is_team}")

    print("\nBookings in the database:")
    bookings = Booking.query.all()
    for booking in bookings:
        print(f"- Day: {booking.day}, Timeslot: {booking.timeslot}, Email1: {booking.email1}, Email2: {booking.email2}")

print("Database check complete!")
