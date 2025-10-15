from rest_framework import serializers
from .models import User, AccidentReport

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'is_driver', 'is_bystander']

class AccidentReportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AccidentReport
        fields = ['id', 'user', 'latitude', 'longitude', 'severity', 'description', 'timestamp', 'reported_via']
