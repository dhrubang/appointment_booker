from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, current_app
from application import db
from application.models import Appointment, User, ProfessionalProfile
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('appointment', __name__)

@bp.route('/appointments', methods=['GET', 'POST'])
def book_appointment():
    # For GET, show the form without requiring JWT
    professionals = User.query.filter_by(role='professional').join(ProfessionalProfile).filter(ProfessionalProfile.approved == True).all()
    if request.method == 'GET':
        logger.debug(f"Loading appointment form. Session: {session}")
        return render_template('appointment.html', professionals=professionals)

    # For POST, require JWT (via session or header)
    current_user_id = None
    if request.is_json:
        logger.debug("API request detected, checking JWT in headers")
        try:
            verify_jwt_in_request(locations=['headers'])
            current_user_id = get_jwt_identity()
        except Exception as e:
            logger.error(f"API JWT verification failed: {str(e)}")
            return jsonify({'msg': 'Invalid or missing JWT token'}), 401
    elif 'access_token' in session:
        logger.debug(f"Browser request, found access_token in session: {session['access_token']}")
        try:
            request.environ['HTTP_AUTHORIZATION'] = f"Bearer {session['access_token']}"
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
        except Exception as e:
            logger.error(f"Session JWT verification failed: {str(e)}")
            return render_template('appointment.html', error='Please log in to book an appointment (invalid token)', professionals=professionals)
    else:
        logger.warning("No access_token in session")
        return render_template('appointment.html', error='Please log in to book an appointment', professionals=professionals)

    if not current_user_id:
        logger.warning("No current_user_id after JWT verification")
        if request.is_json:
            return jsonify({'msg': 'Missing Authorization Header'}), 401
        return render_template('appointment.html', error='Please log in to book an appointment', professionals=professionals)

    # Fetch user details from database
    user = User.query.get(int(current_user_id))
    if not user:
        logger.error(f"User not found for ID: {current_user_id}")
        if request.is_json:
            return jsonify({'msg': 'User not found'}), 401
        return render_template('appointment.html', error='User not found', professionals=professionals)

    if user.role != 'customer':
        logger.debug(f"User {current_user_id} attempted to book but is not a customer")
        if request.is_json:
            return jsonify({'message': 'Only customers can book appointments'}), 403
        return render_template('appointment.html', error='Only customers can book appointments', professionals=professionals)

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    professional_id = data.get('professional_id')
    date_time_str = data.get('date_time')
    message = data.get('message')

    # Validate inputs
    if not all([professional_id, date_time_str]):
        logger.debug(f"Missing fields: professional_id={professional_id}, date_time={date_time_str}")
        if request.is_json:
            return jsonify({'message': 'Missing required fields'}), 400
        return render_template('appointment.html', error='Please fill in all required fields', professionals=professionals)

    try:
        professional_id = int(professional_id)
    except ValueError:
        logger.debug(f"Invalid professional_id: {professional_id}")
        if request.is_json:
            return jsonify({'message': 'Professional ID must be a number'}), 400
        return render_template('appointment.html', error='Professional ID must be a number', professionals=professionals)

    try:
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        logger.debug(f"Invalid date format: {date_time_str}")
        if request.is_json:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD HH:MM'}), 400
        return render_template('appointment.html', error='Invalid date format. Use YYYY-MM-DD HH:MM', professionals=professionals)

    professional = User.query.filter_by(id=professional_id, role='professional').first()
    if not professional or not professional.profile or not professional.profile.approved:
        logger.debug(f"Invalid or unapproved professional: {professional_id}")
        if request.is_json:
            return jsonify({'message': 'Invalid or unapproved professional'}), 400
        return render_template('appointment.html', error='Invalid or unapproved professional', professionals=professionals)

    try:
        appointment = Appointment(
            customer_id=int(current_user_id),
            professional_id=professional_id,
            date_time=date_time,
            message=message,
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()
    except Exception as e:
        logger.error(f"Database error during appointment creation: {str(e)}")
        if request.is_json:
            return jsonify({'message': 'Failed to book appointment due to server error'}), 500
        return render_template('appointment.html', error='Failed to book appointment. Please try again.', professionals=professionals)

    try:
        from task import send_appointment_email
        send_appointment_email.delay(
            professional.email,
            f"New Appointment Request from {user.name}",
            f"You have a new appointment request for {date_time_str}. Message: {message}"
        )
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        # Don't fail the booking if email fails
        pass

    if request.is_json:
        return jsonify({'message': 'Appointment booked successfully'}), 201
    return redirect(url_for('auth.index'))

@bp.route('/appointments/my', methods=['GET'])
@jwt_required()
def my_appointments():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'message': 'User not found'}), 401

    try:
        if user.role == 'customer':
            appointments = Appointment.query.filter_by(customer_id=current_user_id).all()
        else:  # professional
            appointments = Appointment.query.filter_by(professional_id=current_user_id).all()

        return jsonify([{
            'id': a.id,
            'customer': a.customer.name,
            'professional': a.professional.name,
            'date_time': a.date_time.isoformat(),
            'status': a.status,
            'message': a.message
        } for a in appointments]), 200
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        return jsonify({'message': 'Failed to fetch appointments'}), 500

@bp.route('/professionals')
def list_professionals():
    try:
        professionals = User.query.filter_by(role='professional').join(ProfessionalProfile).filter(ProfessionalProfile.approved == True).all()
        return render_template('professionals.html', professionals=professionals)
    except Exception as e:
        logger.error(f"Error listing professionals: {str(e)}")
        return render_template('professionals.html', error='Failed to load professionals')