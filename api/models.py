import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    is_driver = models.BooleanField(default=False)
    is_bystander = models.BooleanField(default=False)

# Accident Report
class AccidentReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    severity = models.CharField(max_length=50, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    reported_via = models.CharField(max_length=20, choices=[
        ('sensor', 'Sensor'),
        ('voice', 'Voice'),
        ('manual', 'Manual')
    ], default='sensor')

    def __str__(self):
        return f"{self.user} - {self.timestamp}"


class BLEAlert(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    message = models.TextField(default="Emergency detected nearby!")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=20, default="unknown", choices=[
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High')
    ])
    location_name = models.CharField(max_length=255, blank=True, null=True)
    broadcast_duration = models.IntegerField(default=30)  # seconds
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default="broadcast", choices=[
        ('broadcast', 'Broadcast'),
        ('received', 'Received'),
        ('expired', 'Expired')
    ])

    def __str__(self):
        return f"BLE Alert: {self.message[:50]}..."

    class Meta:
        ordering = ['-timestamp']


class CloudAlert(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    device_token = models.TextField()
    title = models.CharField(max_length=255, default="Emergency Alert")
    alert_message = models.TextField(default="Emergency alert!")
    data = models.JSONField(default=dict, blank=True)  # Store additional data
    is_emergency = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default="sent", choices=[
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read')
    ])
    failure_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Cloud Alert: {self.title}"

    class Meta:
        ordering = ['-timestamp']