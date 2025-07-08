from rest_framework import serializers
from .models import User, ProfessionalProfile, ChatRequest, Message, Appointment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'phone']

class ProfessionalProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProfessionalProfile
        fields = ['id', 'user', 'service_type', 'service_details', 'experience', 'approved', 'website']

class ChatRequestSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    professional = UserSerializer(read_only=True)

    class Meta:
        model = ChatRequest
        fields = ['id', 'customer', 'professional', 'status', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat_request', 'sender', 'content', 'timestamp']

class AppointmentSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    professional = UserSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'chat_request', 'customer', 'professional', 'datetime', 'details', 'status', 'created_at', 'remarks']