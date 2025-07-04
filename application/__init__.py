from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import os

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Configurations
    app.config['SECRET_KEY'] = 'your-secret-key'  # Ensure this is present
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'  # Change in production
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your Gmail
    app.config['MAIL_PASSWORD'] = 'your-app-password'     # Replace with Gmail App Password
    app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Create instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Register blueprints
    from application.views import auth, appointment
    app.register_blueprint(auth.bp)
    app.register_blueprint(appointment.bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app