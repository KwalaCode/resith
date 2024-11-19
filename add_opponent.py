import os
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Create an opponent user
    opponent = User(email='opponent@example.com', is_team=False)
    opponent.set_password('opponent123')
    db.session.add(opponent)
    db.session.commit()
    print("Opponent user added successfully!")

print("Opponent creation complete!")
