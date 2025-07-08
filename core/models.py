from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import pytz

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role='customer', phone=''):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            role=role,
            phone=phone
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, role='admin'):
        user = self.create_user(
            email=email,
            name=name,
            password=password,
            role=role
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=[('customer', 'Customer'), ('professional', 'Professional'), ('admin', 'Admin')])
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

class ProfessionalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    service_type = models.CharField(max_length=100)
    service_details = models.TextField()
    experience = models.IntegerField(default=0)
    website = models.URLField(blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.name} - {self.service_type}"

class ChatRequest(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_requests_sent')
    professional = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_requests_received')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"ChatRequest from {self.customer} to {self.professional} ({self.status})"

class Message(models.Model):
    chat_request = models.ForeignKey(ChatRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"

class Appointment(models.Model):
    chat_request = models.ForeignKey(ChatRequest, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_appointments')
    professional = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_appointments')
    datetime = models.DateTimeField()
    details = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('deleted', 'Deleted'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True, help_text="Important information or medication details (editable by professional only)")

    def update_status_if_past(self):
        ist = pytz.timezone('Asia/Kolkata')
        current_time = timezone.now().astimezone(ist)
        appointment_time = self.datetime.astimezone(ist)
        if appointment_time < current_time and self.status in ['pending', 'approved']:
            self.status = 'completed'
            self.save()

    def __str__(self):
        return f"Appointment with {self.professional} for {self.customer} on {self.datetime}"