from celery_config import make_celery
from application import create_app, mail
from flask_mail import Message

app = create_app()
celery = make_celery(app)

@celery.task
def send_appointment_email(recipient, subject, body):
    with app.app_context():
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)