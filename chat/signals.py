from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message, Group

# --- New Message Notification ---
@receiver(post_save, sender=Message)
def notify_on_new_message(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    room_group_name = f"chat_{instance.group.id}"

    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            "type": "new_message_notification",
            "message": instance.content,
            "sender": instance.sender.username,
            "group_id": instance.group.id,
        }
    )


# --- Group Membership Join/Leave Notifications ---
@receiver(m2m_changed, sender=Group.members.through)
def group_membership_changed(sender, instance, action, pk_set, **kwargs):
    channel_layer = get_channel_layer()

    if action == "post_add":
        for pk in pk_set:
            async_to_sync(channel_layer.group_send)(
                f"chat_{instance.id}",
                {
                    "type": "group_notification",
                    "event": "user_joined",
                    "user_id": pk,
                    "group_id": instance.id,
                }
            )

    elif action == "post_remove":
        for pk in pk_set:
            async_to_sync(channel_layer.group_send)(
                f"chat_{instance.id}",
                {
                    "type": "group_notification",
                    "event": "user_left",
                    "user_id": pk,
                    "group_id": instance.id,
                }
            )
