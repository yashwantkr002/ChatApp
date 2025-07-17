from django.contrib.auth.models import AbstractUser
from django.db import models
from user.CustomUserManager import CustomUserManager

class CustomUser(AbstractUser):
    # Core status fields
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # Identity fields
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    profile_picture = models.URLField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Invitation system
    invited_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    # Attach the custom manager
    objects = CustomUserManager()

    # Auth customization
    USERNAME_FIELD = 'email'  # Use email for login
    REQUIRED_FIELDS = ['phone']  # Only phone required for superuser

    def save(self, *args, **kwargs):
        # Ensure email is set
        if not self.email and self.phone:
            self.email = f"{self.phone}@example.com"
        # Ensure username is unique and set (required by AbstractUser)
        if not self.username:
            base_username = self.email.split('@')[0] if self.email else str(self.phone)
            unique_username = base_username
            counter = 1
            while CustomUser.objects.filter(username=unique_username).exclude(pk=self.pk).exists():
                unique_username = f"{base_username}{counter}"
                counter += 1
            self.username = unique_username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
