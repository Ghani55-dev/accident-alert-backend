from django.urls import path
from .views import AccidentReportView
from .views import VoiceAccidentReportView, SensorAccidentReportView, BLEAlertView, CloudAlertView
urlpatterns = [
    path('accidents/', AccidentReportView.as_view(), name='accident_reports'),
    path('accidents/voice/', VoiceAccidentReportView.as_view(), name='voice_accident'),
    path('accidents/sensor/', SensorAccidentReportView.as_view(), name='sensor_accident'),
    path('accidents/ble-alert/', BLEAlertView.as_view(), name='ble_alert'),
    path('accidents/cloud-alert/', CloudAlertView.as_view(), name='cloud_alert'),

]