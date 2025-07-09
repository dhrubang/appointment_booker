# Simple Appointment Booking System

A web application designed to facilitate user registration, authentication, and appointment management for both customers and professionals.

## 📋 Description

The Simple Appointment Booking System is a scalable and user-friendly web application that provides:

- **User Registration & Authentication**: Secure registration with validated phone numbers and experience levels
- **Appointment Management**: Book, view, and manage appointments
- **Chat System**: Manage chat requests with initial messages
- **Personalized Dashboards**: Tailored experiences for customers and professionals
- **Admin Panel**: Administrative tools for system management

## 🚀 Tech Stack

### Backend
- **Python 3.x**
- **Django** (Web Framework)
- **Django REST Framework** (API)
- **Celery** (Task Queue, if used with celery.py)

### Frontend
- **HTML5**
- **Tailwind CSS** (via CDN for styling)

### Database
- **SQLite** (via db.sqlite3)

### Other Tools
- **Git** (Version Control)

## 📦 Installation & Setup

### Prerequisites
- Python 3.x installed
- Git installed
- Internet connection for dependencies

### Steps to Run the Project

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dhrubang/appointment_booker.git
   cd appointment-booker
   ```

2. **Create a Virtual Environment** (Recommended)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Create requirements.txt if not present
   echo "django>=4.0,<5.0
   djangorestframework>=3.14.0" > requirements.txt
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Apply Database Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```

6. **Access the Application**
   Open your browser and navigate to: `http://127.0.0.1:8000/`

### Deactivate Virtual Environment
When you're done working on the project:
```bash
deactivate
```

## 🔧 Configuration

### Database
- The project uses **SQLite** by default (`db.sqlite3`)
- For production environments, consider switching to **PostgreSQL** or **MySQL** in `appointment_system/settings.py`

### Styling
- **Tailwind CSS** is included via CDN in templates
- Ensure internet connectivity for proper styling

## 📁 Project Structure

```
appointment-booker/
├── appointment_system/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── db.sqlite3
├── manage.py
├── requirements.txt
└── README.md
```

## 🔐 Features

- **User Authentication**: Secure login and registration system
- **Phone Number Validation**: Ensures valid contact information
- **Experience Level Tracking**: For professional users
- **Appointment Booking**: Full CRUD operations for appointments
- **Chat Management**: Handle customer-professional communications
- **Dashboard**: Personalized user interfaces
- **Admin Interface**: Built-in Django admin panel

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add some amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Issues and Suggestions
- Please open an issue on GitHub for bugs or feature requests
- Check existing issues before creating new ones

## 📝 License

This project is open source. Please check the repository for license details.

## 📞 Support

For support, issues, or questions:
- Open an issue on [GitHub](https://github.com/dhrubang/appointment_booker/issues)
- Contact the developer through the repository

## 📅 Updates

- **Last Updated**: 2025-07-09 at 06:03 AM IST
- **Version**: 1.0.0

## 🔮 Future Enhancements

- Integration with payment gateways
- Email notifications
- Advanced scheduling features
- Mobile app development
- Multi-language support

---

**Happy Coding! 🚀**
