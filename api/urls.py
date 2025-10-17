from django.urls import path
from .views import AccidentReportView
from .views import VoiceAccidentReportView, SensorAccidentReportView, BLEAlertView, CloudAlertView, BLEAlertListView, CloudAlertListView

from . import views
urlpatterns = [
    path('accidents/', AccidentReportView.as_view(), name='accident_reports'),
    path('accidents/voice/', VoiceAccidentReportView.as_view(), name='voice_accident'),
    path('accidents/sensor/', SensorAccidentReportView.as_view(), name='sensor_accident'),
    # path('accidents/ble-alert/', BLEAlertView.as_view(), name='ble_alert'),
    # path('accidents/cloud-alert/', CloudAlertView.as_view(), name='cloud_alert'),
    # path('accidents/ble-alerts/', BLEAlertListView.as_view(), name='ble-alerts'),
    # path('accidents/cloud-alerts/', CloudAlertListView.as_view(), name='cloud-alerts'),
     # BLE Alert URLs
    path('accidents/ble-alert/', views.BLEAlertView.as_view(), name='ble_alert'),
    path('accidents/ble-alerts/', views.BLEAlertListView.as_view(), name='ble_alerts_list'),
    path('accidents/ble-alerts/<uuid:alert_id>/', views.BLEAlertDetailView.as_view(), name='ble_alert_detail'),
    
    # Cloud Alert URLs  
    path('accidents/cloud-alert/', views.CloudAlertView.as_view(), name='cloud_alert'),
    path('accidents/cloud-alerts/', views.CloudAlertListView.as_view(), name='cloud_alerts_list'),
    path('accidents/cloud-alerts/<uuid:alert_id>/', views.CloudAlertDetailView.as_view(), name='cloud_alert_detail'),
    
    # Statistics
    path('accidents/alert-statistics/', views.AlertStatisticsView.as_view(), name='alert_statistics'),
    
    path('accidents/emergency/notify/', views.emergency_notify, name='emergency_notify'),
    

]