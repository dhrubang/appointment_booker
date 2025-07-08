from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db import models, transaction
from .models import User, ProfessionalProfile, ChatRequest, Message, Appointment
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .serializers import UserSerializer, ProfessionalProfileSerializer, ChatRequestSerializer, MessageSerializer, AppointmentSerializer
from django.utils import timezone
import pytz
import logging

# Set up logging
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'customer':
                return redirect('customer_dashboard')
            elif user.role == 'professional':
                return redirect('professional_dashboard')
        messages.error(request, 'Invalid email or password')
    current_time = timezone.now()  # UTC
    return render(request, 'login.html', {'current_time': current_time})

def register_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        name = request.POST['name']
        password = request.POST['password']
        role = request.POST['role']
        phone = request.POST.get('phone', '')
        service_type = request.POST.get('service_type', '')
        service_details = request.POST.get('service_details', '')
        experience = request.POST.get('experience', '0')
        website = request.POST.get('website', '')

        # Validate phone (only numbers if provided)
        if phone and not phone.isdigit():
            messages.error(request, 'Phone number must contain only digits.')
            return render(request, 'register.html', {'current_time': timezone.now()})

        # Validate experience (non-negative number)
        try:
            experience = int(experience)
            if experience < 0:
                messages.error(request, 'Experience must be a non-negative number.')
                return render(request, 'register.html', {'current_time': timezone.now()})
        except ValueError:
            messages.error(request, 'Experience must be a valid number.')
            return render(request, 'register.html', {'current_time': timezone.now()})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered. Please use a different email.')
            return render(request, 'register.html', {'current_time': timezone.now()})

        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, name=name, password=password, role=role, phone=phone)
                if role == 'professional':
                    ProfessionalProfile.objects.create(
                        user=user,
                        service_type=service_type,
                        service_details=service_details,
                        experience=experience,
                        website=website
                    )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'register.html', {'current_time': timezone.now()})
    current_time = timezone.now()  # UTC
    return render(request, 'register.html', {'current_time': current_time})

@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'customer':
        return redirect('customer_dashboard')
    else:
        return redirect('professional_dashboard')

@login_required
def admin_dashboard_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    customer_query = request.GET.get('customer_query', '')
    professional_query = request.GET.get('professional_query', '')
    customers = User.objects.filter(role='customer')
    if customer_query:
        customers = customers.filter(models.Q(name__icontains=customer_query) | models.Q(email__icontains=customer_query))
    approved_professionals = User.objects.filter(role='professional', profile__approved=True)
    pending_professionals = User.objects.filter(role='professional', profile__approved=False)
    if professional_query:
        approved_professionals = approved_professionals.filter(
            models.Q(name__icontains=professional_query) | models.Q(email__icontains=professional_query) | models.Q(profile__service_type__icontains=professional_query)
        )
        pending_professionals = pending_professionals.filter(
            models.Q(name__icontains=professional_query) | models.Q(email__icontains=professional_query) | models.Q(profile__service_type__icontains=professional_query)
        )
    current_time = timezone.now()  # UTC
    return render(request, 'admin_dashboard.html', {
        'customers': customers,
        'approved_professionals': approved_professionals,
        'pending_professionals': pending_professionals,
        'current_time': current_time
    })

@login_required
def customer_dashboard_view(request):
    if request.user.role != 'customer':
        return HttpResponseForbidden()
    service_query = request.GET.get('service_query', '')
    professionals = User.objects.filter(role='professional', profile__approved=True)
    if service_query:
        professionals = professionals.filter(profile__service_type__icontains=service_query)
    chat_requests = ChatRequest.objects.filter(customer=request.user)
    ongoing_chats = chat_requests.filter(status='approved')
    current_time = timezone.now()  # UTC
    # Delete pending appointments past their scheduled time
    Appointment.objects.filter(customer=request.user, status='pending', datetime__lt=current_time).delete()
    appointments = Appointment.objects.filter(customer=request.user, status='approved')
    pending_appointments = Appointment.objects.filter(customer=request.user, status='pending', datetime__gte=current_time)
    upcoming_appointments = appointments.filter(datetime__gte=current_time)
    past_appointments = appointments.filter(datetime__lt=current_time)
    
    return render(request, 'customer_dashboard.html', {
        'professionals': professionals,
        'chat_requests': chat_requests.exclude(status='approved'),
        'ongoing_chats': ongoing_chats,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'current_time': current_time
    })

@login_required
def professional_dashboard_view(request):
    if request.user.role != 'professional':
        return HttpResponseForbidden()
    try:
        is_approved = request.user.profile.approved
    except ProfessionalProfile.DoesNotExist:
        logger.error(f"User {request.user.email} has no ProfessionalProfile")
        messages.error(request, 'Your professional profile is incomplete. Please contact support.')
        return redirect('login')
    chat_requests = ChatRequest.objects.filter(professional=request.user).prefetch_related('messages')
    ongoing_chats = chat_requests.filter(status='approved')
    current_time = timezone.now()  # UTC
    # Delete pending appointments past their scheduled time
    Appointment.objects.filter(professional=request.user, status='pending', datetime__lt=current_time).delete()
    appointments = Appointment.objects.filter(professional=request.user, status='approved')
    pending_appointments = Appointment.objects.filter(professional=request.user, status='pending', datetime__gte=current_time)
    upcoming_appointments = appointments.filter(datetime__gte=current_time)
    past_appointments = appointments.filter(datetime__lt=current_time)
    
    return render(request, 'professional_dashboard.html', {
        'chat_requests': chat_requests.exclude(status='approved'),
        'ongoing_chats': ongoing_chats,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'is_approved': is_approved,
        'current_time': current_time
    })

@login_required
def customer_detail_view(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    customer = get_object_or_404(User, id=user_id, role='customer')
    current_time = timezone.now()  # UTC
    # Delete pending appointments past their scheduled time
    Appointment.objects.filter(customer=customer, status='pending', datetime__lt=current_time).delete()
    appointments = Appointment.objects.filter(customer=customer, status='approved')
    pending_appointments = Appointment.objects.filter(customer=customer, status='pending', datetime__gte=current_time)
    upcoming_appointments = appointments.filter(datetime__gte=current_time)
    past_appointments = appointments.filter(datetime__lt=current_time)
    chat_requests = ChatRequest.objects.filter(customer=customer)
    total_appointments = appointments.count()
    completed_appointments = appointments.filter(datetime__lt=current_time).count()
    if request.method == 'POST' and 'delete' in request.POST:
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('admin_dashboard')
    return render(request, 'customer_detail.html', {
        'customer': customer,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'chat_requests': chat_requests,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'current_time': current_time
    })

@login_required
def professional_detail_view(request, user_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden()
    professional = get_object_or_404(User, id=user_id, role='professional')
    current_time = timezone.now()  # UTC
    # Delete pending appointments past their scheduled time
    Appointment.objects.filter(professional=professional, status='pending', datetime__lt=current_time).delete()
    appointments = Appointment.objects.filter(professional=professional, status='approved')
    pending_appointments = Appointment.objects.filter(professional=professional, status='pending', datetime__gte=current_time)
    upcoming_appointments = appointments.filter(datetime__gte=current_time)
    past_appointments = appointments.filter(datetime__lt=current_time)
    chat_requests = ChatRequest.objects.filter(professional=professional)
    total_appointments = appointments.count()
    completed_appointments = appointments.filter(datetime__lt=current_time).count()
    if request.method == 'POST':
        if 'approve' in request.POST:
            professional.profile.approved = True
            professional.profile.save()
            messages.success(request, 'Professional approved.')
        elif 'delete' in request.POST:
            professional.delete()
            messages.success(request, 'Professional deleted.')
        return redirect('admin_dashboard')
    return render(request, 'professional_detail.html', {
        'professional': professional,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'chat_requests': chat_requests,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'current_time': current_time
    })

@login_required
def chat_request_view(request, professional_id):
    if request.user.role != 'customer':
        return HttpResponseForbidden()
    professional = get_object_or_404(User, id=professional_id, role='professional', profile__approved=True)
    if request.method == 'POST':
        message_content = request.POST.get('message', '')
        if not message_content:
            messages.error(request, 'Message is required.')
            return redirect('customer_dashboard')
        existing_chat_request = ChatRequest.objects.filter(
            customer=request.user,
            professional=professional,
            status__in=['pending', 'approved']
        ).first()
        if existing_chat_request:
            Message.objects.create(
                chat_request=existing_chat_request,
                sender=request.user,
                content=message_content
            )
            messages.success(request, 'Message added to existing chat request.')
        else:
            chat_request = ChatRequest.objects.create(
                customer=request.user,
                professional=professional,
                status='pending'
            )
            Message.objects.create(
                chat_request=chat_request,
                sender=request.user,
                content=message_content
            )
            messages.success(request, 'Chat request sent.')
        return redirect('customer_dashboard')
    current_time = timezone.now()  # UTC
    return render(request, 'chat_request.html', {'professional': professional, 'current_time': current_time})

@login_required
def chat_window_view(request, chat_request_id):
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id)
    if request.user != chat_request.customer and request.user != chat_request.professional:
        return HttpResponseForbidden()
    if request.user == chat_request.professional and request.method == 'POST' and 'action' in request.POST:
        action = request.POST.get('action')
        if action in ['approved', 'rejected']:
            chat_request.status = action
            chat_request.save()
            messages.success(request, f'Chat request {action}.')
            return redirect('professional_dashboard')
    if request.method == 'POST' and 'message' in request.POST:
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                chat_request=chat_request,
                sender=request.user,
                content=content
            )
            messages.success(request, 'Message sent.')
        else:
            messages.error(request, 'Message cannot be empty.')
        return redirect('chat_window', chat_request_id=chat_request_id)
    if request.user == chat_request.professional and request.method == 'POST' and 'remarks' in request.POST:
        appointment_id = request.POST.get('appointment_id')
        remarks = request.POST.get('remarks')
        appointment = get_object_or_404(Appointment, id=appointment_id, professional=request.user)
        appointment.remarks = remarks
        appointment.save()
        messages.success(request, 'Remarks updated successfully.')
        return redirect('chat_window', chat_request_id=chat_request_id)
    messages_list = chat_request.messages.order_by('timestamp')
    current_time = timezone.now()  # UTC
    # Delete pending appointments past their scheduled time
    chat_request.appointments.filter(status='pending', datetime__lt=current_time).delete()
    appointments = chat_request.appointments.filter(status='approved')
    pending_appointments = chat_request.appointments.filter(status='pending', datetime__gte=current_time)
    return render(request, 'chat_window.html', {
        'chat_request': chat_request,
        'messages': messages_list,
        'appointments': appointments,
        'pending_appointments': pending_appointments,
        'current_time': current_time
    })

@login_required
def appointment_request_view(request, chat_request_id):
    if request.user.role != 'professional':
        return HttpResponseForbidden()
    chat_request = get_object_or_404(ChatRequest, id=chat_request_id, professional=request.user, status='approved')
    current_time = timezone.now()  # UTC
    if request.method == 'POST':
        datetime_str = request.POST['datetime']
        details = request.POST['details']
        remarks = request.POST.get('remarks', '')
        try:
            # Parse datetime with seconds
            naive_datetime = timezone.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
            datetime = timezone.make_aware(naive_datetime, timezone=pytz.UTC)
            if datetime <= current_time:
                messages.error(request, 'Appointment date and time must be in the future.')
                return render(request, 'appointment_request.html', {'chat_request': chat_request, 'current_time': current_time})
            appointment = Appointment.objects.create(
                chat_request=chat_request,
                customer=chat_request.customer,
                professional=chat_request.professional,
                datetime=datetime,
                details=details,
                status='pending',
                created_at=current_time,
                remarks=remarks
            )
            messages.success(request, 'Appointment request sent.')
            return redirect('chat_window', chat_request_id=chat_request_id)
        except ValueError:
            try:
                # Fallback for datetime without seconds
                naive_datetime = timezone.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
                datetime = timezone.make_aware(naive_datetime, timezone=pytz.UTC)
                if datetime <= current_time:
                    messages.error(request, 'Appointment date and time must be in the future.')
                    return render(request, 'appointment_request.html', {'chat_request': chat_request, 'current_time': current_time})
                appointment = Appointment.objects.create(
                    chat_request=chat_request,
                    customer=chat_request.customer,
                    professional=chat_request.professional,
                    datetime=datetime,
                    details=details,
                    status='pending',
                    created_at=current_time,
                    remarks=remarks
                )
                messages.success(request, 'Appointment request sent.')
                return redirect('chat_window', chat_request_id=chat_request_id)
            except ValueError:
                messages.error(request, 'Invalid date format. Please use YYYY-MM-DD HH:MM.')
                return render(request, 'appointment_request.html', {'chat_request': chat_request, 'current_time': current_time})
    return render(request, 'appointment_request.html', {'chat_request': chat_request, 'current_time': current_time})

@login_required
def manage_appointment_view(request, appointment_id):
    if request.user.role != 'customer':
        return HttpResponseForbidden()
    appointment = get_object_or_404(Appointment, id=appointment_id, customer=request.user)
    current_time = timezone.now()  # UTC
    if request.method == 'POST':
        action = request.POST.get('action')
        if appointment.datetime <= current_time:
            messages.error(request, 'Cannot modify appointment after its scheduled time.')
            return render(request, 'manage_appointment.html', {'appointment': appointment, 'current_time': current_time})
        if action == 'approve':
            appointment.status = 'approved'
            appointment.save()
            messages.success(request, 'Appointment approved.')
        elif action == 'reject':
            appointment.delete()
            messages.success(request, 'Appointment rejected and deleted.')
        return redirect('customer_dashboard')
    return render(request, 'manage_appointment.html', {'appointment': appointment, 'current_time': current_time})

def logout_view(request):
    logout(request)
    return redirect('login')

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class ProfessionalProfileViewSet(viewsets.ModelViewSet):
    queryset = ProfessionalProfile.objects.all()
    serializer_class = ProfessionalProfileSerializer
    permission_classes = [IsAuthenticated]

class ChatRequestViewSet(viewsets.ModelViewSet):
    queryset = ChatRequest.objects.all()
    serializer_class = ChatRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ChatRequest.objects.all()
        elif user.role == 'customer':
            return ChatRequest.objects.filter(customer=user)
        else:
            return ChatRequest.objects.filter(professional=user)

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Message.objects.all()
        return Message.objects.filter(chat_request__customer=user) | Message.objects.filter(chat_request__professional=user)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        current_time = timezone.now()  # UTC
        Appointment.objects.filter(status='pending', datetime__lt=current_time).delete()
        if user.role == 'admin':
            return Appointment.objects.all()
        elif user.role == 'customer':
            return Appointment.objects.filter(customer=user, status='approved')
        else:
            return Appointment.objects.filter(professional=user, status='approved')