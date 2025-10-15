import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

# Optional: Custom User
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
