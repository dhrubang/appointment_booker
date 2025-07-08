from celery import shared_task
from .models import Appointment

@shared_task
def process_appointment(appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    # Simulate processing (e.g., sending email)
    print(f"Processing appointment {appointment_id} for {appointment.customer.name} with {appointment.professional.name}")
    return f"Appointment {appointment_id} processed"