from django.urls import path, include

from . import views
from user import views as user_views
urlpatterns = [
    path('', views.index, name='index'),

    # User Authentication and profile
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

    # User Chats  Urls
    path('home/', views.chat_home_view, name='home'),

    path('chat/<int:user_id>/', views.chat_detail_view, name='chat_detail'),
    path('chat/start/', views.start_chat_view, name='start_chat'),
    path('chat/group/', views.start_group_view, name='start_group'),


    # search freand add friend list
    path('search/', views.search_user_view, name='search_user'),
    path('add-friend/<int:user_id>/', views.add_friend, name='add_friend'),

]
