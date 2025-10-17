from django.contrib import admin
from .models import User, AccidentReport, BLEAlert, CloudAlert

admin.site.register(User)
admin.site.register(AccidentReport)

@admin.register(BLEAlert)
class BLEAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'severity', 'latitude', 'longitude', 'status', 'timestamp')
    list_filter = ('severity', 'status', 'timestamp')
    search_fields = ('message', 'location_name')
    readonly_fields = ('id', 'timestamp')
    list_per_page = 20

@admin.register(CloudAlert)
class CloudAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'short_device_token', 'is_emergency', 'status', 'timestamp')
    list_filter = ('is_emergency', 'status', 'timestamp')
    search_fields = ('title', 'alert_message', 'device_token')
    readonly_fields = ('id', 'timestamp')
    list_per_page = 20

    def short_device_token(self, obj):
        return f"{obj.device_token[:20]}..." if obj.device_token else "None"
    short_device_token.short_description = 'Device Token'
