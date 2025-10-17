from rest_framework import serializers
from .models import AccidentReport, User  # ✅ Import custom User model
from .models import BLEAlert, CloudAlert

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # ✅ Use custom User model
        fields = ['id', 'username', 'email', 'phone_number', 'is_driver', 'is_bystander']

class AccidentReportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AccidentReport
        fields = ['id', 'user', 'latitude', 'longitude', 'severity', 'description', 'timestamp', 'reported_via']
        

class BLEAlertSerializer(serializers.ModelSerializer):
    formatted_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = BLEAlert
        fields = '__all__'
    
    def get_formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")


class CloudAlertSerializer(serializers.ModelSerializer):
    formatted_timestamp = serializers.SerializerMethodField()
    short_device_token = serializers.SerializerMethodField()
    
    class Meta:
        model = CloudAlert
        fields = '__all__'
    
    def get_formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_short_device_token(self, obj):
        if obj.device_token:
            return f"{obj.device_token[:20]}..." if len(obj.device_token) > 20 else obj.device_token
        return "Unknown"
