
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from chat.models import *

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'phone', 'is_staff', 'is_online', 'last_seen']
    list_filter = ['is_staff', 'is_online', 'last_seen']
    search_fields = ['username', 'email', 'phone',]
    ordering = ['username']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Group)
admin.site.register(Message)
admin.site.register(FileMessage)
admin.site.register(Friend)
admin.site.register(PrivateChat)
admin.site.register(UnreadMessageCount)


