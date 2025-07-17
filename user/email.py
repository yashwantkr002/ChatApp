from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

def send_otp_email(email, otp):
    subject = "OTP Verification - MySite"
    template_name = 'emailTemplate.html'

    context = {
        'otp': otp,
        'email': email,
        'current_year': timezone.now().year,
    }

    html_message = render_to_string(template_name, context)

    email_message = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[email],
    )
    email_message.content_subtype = 'html'  # Set content to HTML
    email_message.send(fail_silently=False)
