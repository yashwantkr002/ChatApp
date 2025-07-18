from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
import time
import pyotp
import re
from .cloudinary_utils import cloudinary_upload  # Assuming you have a utility for Cloudinary uploads
# Create your views here.
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenSerializer
from .email import send_otp_email  # Assuming you have an email utility for sending OTPs

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

# accounts/views.py


def signup_view(request):
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            profile_picture = request.FILES.get('profile_picture')

            # Validate required fields
            if not phone or not re.match(r'^\d{10}$', phone):
                messages.error(request, 'Please enter a valid 10-digit phone number')
                return render(request, 'signup.html')

            if not (phone and email and password):
                messages.error(request, 'Phone, Email, and Password are required')
                return render(request, 'signup.html')

            # validate email format
            if not re.match(r'^[\w.@+-]+$', email):
                messages.error(request, 'Email is not valid')
                return render(request, 'signup.html')

            # validate email uniqueness
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'signup.html')

            # validate phone number uniqueness
            if CustomUser.objects.filter(phone=phone).exists():
                messages.error(request, 'Phone number already exists')
                return render(request, 'signup.html')

            # validate email format
            if not re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z0-9-.]+$', email):
                messages.error(request, 'Email is not valid')
                return render(request, 'signup.html')
            
            # validate password minimum length and complexity
            if not password or len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long')
                return render(request, 'signup.html')
            
            # confirm password match
            if password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return render(request, 'signup.html')
            # validate password complexity
            if not re.search(r'[A-Z]', password):
                messages.error(request, 'Password must contain at least one uppercase letter')
                return render(request, 'signup.html')
            if not re.search(r'[a-z]', password):
                messages.error(request, 'Password must contain at least one lowercase letter')
                return render(request, 'signup.html')
            if not re.search(r'\d', password):
                messages.error(request, 'Password must contain at least one digit')
                return render(request, 'signup.html')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                messages.error(request, 'Password must contain at least one special character')
                return render(request, 'signup.html')

            user = CustomUser.objects.create_user(
                phone=phone,
                email=email,
                password=password,
            )

            if profile_picture:
                result = cloudinary_upload(profile_picture)
                user.profile_picture = result['secure_url'] or ''
            user.is_verified = False
            user.save()

            # Generate pyotp secret & OTP
            otp_secret = pyotp.random_base32()
            otp = pyotp.TOTP(otp_secret).now()

            # Save secret and user_id in session
            request.session['otp_secret'] = otp_secret
            request.session['otp_timestamp'] = int(time.time()) 
            request.session['user_id'] = user.id

            print(f"Generated OTP: {otp} and type of OTP: {type(otp)}")  # Replace with SMS/email send logic
            send_otp_email(email, otp)  # Send OTP via email
            messages.success(request, f'Signup successful! Please verify your OTP sent to {email}.')
            return redirect('otp-verify')
        except Exception as e:
            messages.error(request, f"Signup failed: {str(e)}")
            return render(request, 'signup.html')
    return render(request, 'signup.html')


# OTP verification view
def otp_verify_view(request):
    if request.method == 'POST':
        input_otp = request.POST.get('otp')
        otp_secret = request.session.get('otp_secret')
        otp_timestamp = request.session.get('otp_timestamp')
        user_id = request.session.get('user_id')

        # Check if all required session data is present
        if not all([input_otp, otp_secret, otp_timestamp, user_id]):
            messages.error(request, 'Missing OTP session or expired. Please try again.')
            return redirect('signup')

        # Ensure otp_timestamp is an integer
        try:
            otp_timestamp = int(otp_timestamp)
        except (TypeError, ValueError):
            messages.error(request, 'OTP timestamp error. Please request a new OTP.')
            return redirect('signup')

        # OTP valid for 5 minutes (300 seconds)
        expiry_seconds = 300
        current_time = int(time.time())

        if current_time - otp_timestamp > expiry_seconds:
            messages.error(request, 'OTP has expired. Please send otp again.')
            # You can also regenerate OTP here instead of redirect
            return redirect('signup')

        try:
            totp = pyotp.TOTP(otp_secret)
            if totp.verify(input_otp, valid_window=1):
                try:
                    user = CustomUser.objects.get(id=user_id)
                    user.is_verified = True
                    user.save()
                    login(request, user)

                    # Cleanup session
                    for key in ['otp_secret', 'otp_timestamp', 'user_id']:
                        request.session.pop(key, None)

                    messages.success(request, 'OTP verified. You are now logged in.')
                    return redirect('home')
                except (CustomUser.DoesNotExist, ValueError):
                    messages.error(request, 'User not found.')
                    return redirect('signup')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        except Exception as e:
            messages.error(request, f'OTP verification error: {str(e)}')
    return render(request, 'otp_verify.html')


# Resend OTP view

def resend_otp_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('signup')

    try:
        # Step 1: Fetch user
        user = CustomUser.objects.get(id=user_id)

        # Step 2: Generate new OTP
        otp_secret = pyotp.random_base32()
        otp = pyotp.TOTP(otp_secret).now()

        # Step 3: Store OTP info in session
        request.session['otp_secret'] = otp_secret
        request.session['otp_timestamp'] = int(time.time())

        # Step 4: Send OTP via email
        print(f"🔁 New OTP for {user.phone}: {otp}")
        send_otp_email(user.email, otp)

        # Step 5: Notify user
        messages.success(request, f"A new OTP has been sent. Please check your email: {user.email}")
        return redirect('otp-verify')

    except Exception as e:
        # Generic error handling (e.g., email sending failure)
        print(f"Error while resending OTP: {e}")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('signup')

# Login view
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        user = None

        # Try to find by phone first
        try:
            user_obj = CustomUser.objects.get(phone=identifier)
            user = authenticate(request, email=user_obj.email, password=password)
        except CustomUser.DoesNotExist:
            # Try to authenticate using email
            user = authenticate(request, email=identifier, password=password)

        if user is not None:
            if user.is_verified:
                login(request, user)
                messages.success(request, 'Login successful!')
                if user.first_name not in [None, '']:
                    return redirect('home')
                else:
                    messages.info(request, 'Please complete your profile.')
                    return redirect('complete-profile')  # Replace with your homepage
            else:
                messages.error(request, 'Account not verified via OTP. Please verify first.')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'login.html')

# froget password view
def forget_password_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        try:
            user = CustomUser.objects.get(phone=phone)
            # Generate OTP and send it to the user's phone
            otp_secret = pyotp.random_base32()
            otp = pyotp.TOTP(otp_secret).now()
            # Replace with SMS send logic
            print(f"🔁 OTP for password reset: {otp} and type of OTP: {type(otp)}")  
            send_otp_email(user.email, otp)  # Send OTP via email
            # Save OTP secret in session
            request.session['otp_secret'] = otp_secret
            request.session['otp_timestamp'] = int(time.time())
            request.session['user_id'] = user.id

            messages.success(request, f'OTP sent to your Email: {user.email}. Please verify.')
            return redirect('otp-verify-reset')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Phone number not found.')

    return render(request, 'forget_password.html')


# otp-verify-reset view
def otp_verify_reset_view(request):
    if request.method == 'POST':
        input_otp = request.POST.get('otp', '').strip()
        user_id = request.session.get('user_id')
        otp_secret = request.session.get('otp_secret')
        otp_timestamp = request.session.get('otp_timestamp')

        # Check missing data
        if not all([input_otp, user_id, otp_secret, otp_timestamp]):
            messages.error(request, 'OTP session expired or missing. Please try again.')
            return redirect('forget-password')

        # Ensure otp_timestamp is an integer
        try:
            otp_timestamp = int(otp_timestamp)
        except (TypeError, ValueError):
            messages.error(request, 'OTP timestamp error. Please request a new OTP.')
            return redirect('forget-password')

        # OTP expiry (5 minutes)
        expiry_seconds = 300
        current_time = int(time.time())
        if current_time - otp_timestamp > expiry_seconds:
            messages.error(request, 'OTP has expired. Please request a new one.')
            return redirect('forget-password')

        # Verify OTP
        try:
            user = CustomUser.objects.get(id=user_id)
        except (CustomUser.DoesNotExist, ValueError):
            messages.error(request, "User not found.")
            return redirect('forget-password')

        try:
            totp = pyotp.TOTP(otp_secret)
            # Verify OTP with a small time drift tolerance
            if totp.verify(input_otp, valid_window=1):
                request.session['otp_verified'] = True
                return redirect('reset-password')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        except Exception as e:
            messages.error(request, f"OTP verification error: {str(e)}")
    return render(request, 'otp_verify_reset.html')

# Resend otp very reset view
def resend_otp_reset_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('signup')

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('signup')
    try:
        # Generate new OTP and update session
        otp_secret = pyotp.random_base32()
        otp = pyotp.TOTP(otp_secret).now()

        request.session['otp_secret'] = otp_secret
        request.session['otp_timestamp'] = int(time.time())
        # Send via SMS/email in real application
        print(f"🔁 New OTP for {user.phone}: {otp}")
        send_otp_email(user.email, otp)

        messages.success(request, f"A new OTP has been sent to your Email: {user.email}.")
        return redirect('otp-verify-reset')
    except Exception as e:
        messages.error(request, f"Failed to send OTP: {str(e)}")
        return redirect('signup')


# Reset password view
def reset_password_view(request):
    if not request.session.get('otp_verified'):
        messages.error(request, "OTP verification is required before resetting password.")
        return redirect('forget-password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            messages.error(request, "Both password fields are required.")
            return render(request, 'reset_password.html')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'reset_password.html')
        
        # validate password minimum length and complexity
        if not new_password or len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'reset_password.html')
        if not re.search(r'[A-Z]', new_password):
            messages.error(request, 'Password must contain at least one uppercase letter')
            return render(request, 'reset_password.html')
        if not re.search(r'[a-z]', new_password):
            messages.error(request, 'Password must contain at least one lowercase letter')
            return render(request, 'reset_password.html')
        if not re.search(r'\d', new_password):
            messages.error(request, 'Password must contain at least one digit')
            return render(request, 'reset_password.html')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            messages.error(request, 'Password must contain at least one special character')
            return render(request, 'reset_password.html')


        user_id = request.session.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()

            # Clean up session
            for key in ['otp_verified', 'user_id', 'otp_secret', 'otp_timestamp']:
                request.session.pop(key, None)

            messages.success(request, "Your password has been reset successfully.")
            return redirect('login')

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('forget-password')

    return render(request, 'reset_password.html')


# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')  



# complete profile view
@login_required
def complete_profile_view(request):
    try:
        user = request.user

        if request.method == "POST":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            bio = request.POST.get("bio", "").strip()

            
            if not first_name or not last_name:
                messages.error(request, "First name and last name are required.")
                return render(request, "complete_profile.html", context={'user': user})

            try:
                user.first_name = first_name
                user.last_name = last_name
                user.bio = bio
                user.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("home")  # Redirect to home/dashboard
            except Exception as e:
                messages.error(request, f"Failed to update profile. Please try again later. {e}")
                return render(request, "complete_profile.html", context={'user': user})
        return render(request, "complete_profile.html", context={'user': user})

    except Exception as e:
        messages.error(request, f"An unexpected error occurred. {e}")
        return redirect("login")  # Redirect to login if something fails badly

