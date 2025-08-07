from django.db import models
from user.models import CustomUser

class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(CustomUser, related_name='chat_groups')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PrivateChat(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='private_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_room_id(self):
        # Get the two user IDs, sort them, and join with an underscore
        user_ids = sorted(self.participants.values_list('id', flat=True))
        return f"room_{user_ids[0]}_{user_ids[1]}"

class Message(models.Model):
    # Supports both private and group chat
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, null=True, blank=True)

    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} at {self.timestamp}"

class FileMessage(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=50)  # e.g., image, video, document
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional: link to chat
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.file_type} sent by {self.sender}"

class Friend(models.Model):
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_friend_requests')
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # Prevent duplicate friend requests
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} ➝ {self.to_user} ({self.status})"


