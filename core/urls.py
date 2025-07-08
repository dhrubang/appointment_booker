from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'professionals', views.ProfessionalProfileViewSet)
router.register(r'chat_requests', views.ChatRequestViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'appointments', views.AppointmentViewSet)

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('customer/dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    path('professional/dashboard/', views.professional_dashboard_view, name='professional_dashboard'),
    path('customer/<int:user_id>/', views.customer_detail_view, name='customer_detail'),
    path('professional/<int:user_id>/', views.professional_detail_view, name='professional_detail'),
    path('chat/request/<int:professional_id>/', views.chat_request_view, name='chat_request'),
    path('chat/<int:chat_request_id>/', views.chat_window_view, name='chat_window'),
    path('chat/<int:chat_request_id>/appointment/', views.appointment_request_view, name='appointment_request'),
    path('appointment/<int:appointment_id>/manage/', views.manage_appointment_view, name='manage_appointment'),
    path('api/', include(router.urls)),
]