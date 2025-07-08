from django.contrib import admin
from .models import User, ProfessionalProfile, Appointment

admin.site.register(User)
admin.site.register(ProfessionalProfile)
admin.site.register(Appointment)