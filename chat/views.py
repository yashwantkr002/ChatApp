from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from user.models import CustomUser
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from .models import *
from django.db.models import Q
from django.template.loader import render_to_string
import traceback


def index(request):
    if request.user.is_authenticated:
        # Redirect to home page if logged in
        return redirect('home')
     # If not logged in, show the index page
    return render(request, 'index.html')

@login_required(login_url='/login/')  
def chat_home_view(request):
    try:
        friends = Friend.objects.filter(Q(from_user=request.user) | Q(to_user=request.user))
        contacts = []
        for friend in friends:
            if friend.from_user == request.user:
                contacts.append({'id': friend.to_user.id, 'name': friend.to_user.first_name, 'last_message': 'Hey, what\'s up?', 'profile_picture': friend.to_user.profile_picture})
            else:
                contacts.append({'id': friend.from_user.id, 'name': friend.from_user.first_name, 'last_message': 'Hey, what\'s up?', 'profile_picture': friend.from_user.profile_picture})
        return render(request, 'chat_home.html',{'contacts': contacts})
    except Exception as e:
        print("Error:", e)
        return redirect('login')


@login_required
def chat_detail_view(request, user_id):
    try:
        other_user = get_object_or_404(CustomUser, id=user_id)
        private_chat = PrivateChat.objects.filter(participants=request.user)\
                                          .filter(participants=other_user).first()
        
        if not private_chat:
            private_chat = PrivateChat.objects.create()
            private_chat.participants.add(request.user, other_user)

            # Optional: add a default welcome message
            Message.objects.create(
                private_chat=private_chat,
                sender=request.user,
                content=f"Chat with {other_user.first_name} started!"
            )
        messages_qs = Message.objects.filter(private_chat=private_chat).order_by('timestamp')
        
        friends = Friend.objects.filter(Q(from_user=request.user) | Q(to_user=request.user))
        contacts = []
        for friend in friends:
            if friend.from_user == request.user:
                contacts.append({'id': friend.to_user.id, 'name': friend.to_user.first_name, 'last_message': 'Hey, what\'s up?', 'profile_picture': friend.to_user.profile_picture})
            else:
                contacts.append({'id': friend.from_user.id, 'name': friend.from_user.first_name, 'last_message': 'Hey, what\'s up?', 'profile_picture': friend.from_user.profile_picture})
        room_id = private_chat.get_room_id()
        print(f"Room ID: {room_id}")
        return render(request, 'chat_detail.html', {
            'private_chat': private_chat,
            'messages': messages_qs,
            'other_user': other_user,
            'contacts': contacts,
            'room_id': room_id
        })

    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def start_chat_view(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            other_user = get_object_or_404(CustomUser, id=user_id)

            chat = PrivateChat.objects.filter(participants=request.user)\
                                      .filter(participants=other_user).first()
            if not chat:
                chat = PrivateChat.objects.create()
                chat.participants.add(request.user, other_user)

            return redirect('chat_detail', user_id=other_user.id)
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'start_chat.html', {'users': users})

@login_required
def start_group_view(request):
    if request.method == 'POST':
        try:
            group_name = request.POST.get('group_name')
            user_ids = request.POST.getlist('user_ids')

            if not group_name or not user_ids:
                messages.error(request, "Name & members are required.")
                return redirect('start_group')

            group = Group.objects.create(name=group_name, created_by=request.user)
            group.members.add(request.user)
            for uid in user_ids:
                member = get_object_or_404(CustomUser, id=uid)
                group.members.add(member)

            return redirect('group_chat_detail', group_id=group.id)
        except Exception as e:
            messages.error(request, f"Group creation failed: {str(e)}")

    users = CustomUser.objects.exclude(id=request.user.id)
    return render(request, 'start_group.html', {'users': users})


@login_required
def group_chat_detail_view(request, group_id):
    try:
        group = get_object_or_404(Group, id=group_id)
        if request.user not in group.members.all():
            messages.error(request, "You are not a member of this group.")
            return redirect('home')

        messages_qs = Message.objects.filter(group=group).order_by('timestamp')
        return render(request, 'group_chat_detail.html', {
            'group': group,
            'messages': messages_qs
        })
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('home')




@login_required
def search_user_view(request):
    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        if not query:
            return render(request, "search_results.html", {"error": "Enter email or phone."})

        all_users = CustomUser.objects.filter(
            Q(email__icontains=query) | Q(phone__icontains=query)
        ).exclude(id=request.user.id)

        # Exclude those already related in a friend request
        related_users = Friend.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        ).values_list('from_user_id', 'to_user_id')

        excluded_ids = set()
        for f1, f2 in related_users:
            excluded_ids.add(f1)
            excluded_ids.add(f2)

        results = all_users.exclude(id__in=excluded_ids)

        return render(request, "search_results.html", {
            "results": results,
            "query": query,
        })

    return render(request, "search_results.html", {"error": "Invalid request method."})



@login_required
def add_friend(request, user_id):
    try:
        if request.method == "POST":
            from_user = request.user
            to_user = get_object_or_404(CustomUser, id=user_id)

            if from_user == to_user:
                return HttpResponse("❌ You cannot add yourself.", status=400)

            # Check if request already exists
            existing = Friend.objects.filter(from_user=from_user, to_user=to_user).first()
            if existing:
                return HttpResponse("ℹ️ Friend request already sent.", status=400)

            # Create friend request
            Friend.objects.create(from_user=from_user, to_user=to_user, status='pending')

            # Return a partial HTML response
            html = render_to_string("friend_added_message.html", {"to_user": to_user})
            return HttpResponse(html)

        return HttpResponse("❌ Invalid request method.", status=405)

    except Exception as e:
        # Optional: log the full traceback in development
        traceback.print_exc()
        return HttpResponse(f"⚠️ An unexpected error occurred: {str(e)}", status=500)
