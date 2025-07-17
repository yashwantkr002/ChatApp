from django.shortcuts import render, redirect
from django.contrib.auth import  login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib import messages

# from .models import Message, Chat

def index(request):
    # if not request.user.is_authenticated:
    #     return redirect('login')
    # Assuming you have a Chat model to fetch chats
    # chats = Chat.objects.filter(participants=request.user)
    # return render(request, 'index.html', {'chats': chats})
    return render(request, 'index.html')
from django.shortcuts import redirect

@login_required
def get_private_chat_room(request, username):
    from django.contrib.auth.models import User
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse("User not found", status=404)

    user1_id = request.user.id
    user2_id = other_user.id

    room_id = f'chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}'
    return redirect('chat-room', room_id=room_id)
