# ChatApp

A modern, full-featured Django chat application with OTP-based authentication, email verification, and a premium UI built with Tailwind CSS and Alpine.js.

## Features
- Custom user model with email and phone authentication
- OTP verification for signup and password reset (via email)
- Secure password validation and reset
- Profile completion and editing
- Real-time chat (Channels, WebSockets)
- Responsive, modern UI (Tailwind CSS, Alpine.js)
- Admin panel for user and chat management
- Cloudinary integration for profile pictures

## Requirements
- Python 3.10+
- Django 5.2+
- Channels
- Redis (for Channels layer)
- Tailwind CSS
- Cloudinary account (for image uploads)
- SMTP email credentials (for OTP)

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yashwantkr002/ChatApp.git
   cd ChatApp
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv env
   env\Scripts\activate  # On Windows
   # or
   source env/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your secrets:
     - `SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

5. **Apply migrations:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

8. **Start Redis (for Channels):**
   - Make sure Redis is running on `localhost:6379`.

9. **Access the app:**
   - Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Folder Structure
- `ChatApp/` - Django project settings
- `chat/` - Chat app (models, views, consumers)
- `user/` - User app (custom user, authentication, profile)
- `templates/` - HTML templates
- `theme/` - Tailwind CSS config and static files
- `env/` - Python virtual environment

## Environment Variables Example (`.env.example`)
```
SECRET_KEY=your-django-secret-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
```

## License
MIT

---

**Author:** yashwantkr002

For questions or contributions, open an issue or pull request on GitHub.
