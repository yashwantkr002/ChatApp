from django.urls import path, include

from . import views
from user import views as user_views
urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', user_views.signup_view, name='signup'),
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('otp-verify/', user_views.otp_verify_view, name='otp-verify'),
    path('resend-otp/', user_views.resend_otp_view, name='resend-otp'),
    path('forget-password/', user_views.forget_password_view, name='forget-password'),
    path('otp-verify-reset/', user_views.otp_verify_reset_view, name='otp-verify-reset'),
    path('resend-otp-reset/', user_views.resend_otp_reset_view, name='resend-otp-reset'),
    path('reset-password/', user_views.reset_password_view, name='reset-password'),
    path('complete-profile/', user_views.complete_profile_view, name='complete-profile'),
]
