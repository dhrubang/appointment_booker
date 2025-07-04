from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from application import db
from application.models import User, ProfessionalProfile
from flask_jwt_extended import create_access_token
import bcrypt

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    return render_template('dashboard.html')

@bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    phone = data.get('phone')

    if not all([name, email, password, role]):
        if request.is_json:
            return jsonify({'message': 'Missing fields'}), 400
        return render_template('register.html', error='Missing fields')

    if role not in ['customer', 'professional']:
        if request.is_json:
            return jsonify({'message': 'Invalid role'}), 400
        return render_template('register.html', error='Invalid role')

    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'message': 'Email already exists'}), 400
        return render_template('register.html', error='Email already exists')

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(name=name, email=email, password=hashed_password, role=role, phone=phone)
    db.session.add(user)
    db.session.commit()

    if role == 'professional':
        profile = ProfessionalProfile(user_id=user.id, service_type='General', approved=False)
        db.session.add(profile)
        db.session.commit()

    if request.is_json:
        return jsonify({'message': 'User registered successfully'}), 201
    return redirect(url_for('auth.login'))

@bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        if request.is_json:
            return jsonify({'message': 'Invalid credentials'}), 401
        return render_template('login.html', error='Invalid credentials')

    access_token = create_access_token(identity=str(user.id))
    if request.is_json:
        return jsonify({'access_token': access_token}), 200
    session['access_token'] = access_token
    return render_template('dashboard.html', access_token=access_token)

@bp.route('/auth/logout')
def logout():
    session.pop('access_token', None)
    return redirect(url_for('auth.index'))

@bp.route('/test-email')
def test_email():
    try:
        from application import mail
        from flask_mail import Message
        msg = Message(
            subject="Test Email",
            recipients=['your-test-email@example.com'],
            body="This is a test email from your Appointment Booker!"
        )
        mail.send(msg)
        return jsonify({"message": "Test email sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500