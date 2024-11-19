from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Update this with your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Import and register blueprints
    from .routes import main, auth, booking, admin
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(booking)
    app.register_blueprint(admin)

    return app
