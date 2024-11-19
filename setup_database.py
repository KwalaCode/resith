import os
os.environ['FLASK_APP'] = 'app'  # Make sure this matches your app's name
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models import User, Booking  # Import your models

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

    # Create a test user
    test_user = User(email='test@example.com')
    test_user.set_password('password123')
    db.session.add(test_user)
    db.session.commit()
    print("Test user added successfully!")

print("Database setup complete!")
