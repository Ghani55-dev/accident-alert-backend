from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AccidentReport, User  # ✅ FIX: Import your custom User model
from .serializers import AccidentReportSerializer
from .ml_model import predict_accident
import requests
from django.conf import settings
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .models import BLEAlert, CloudAlert
from .serializers import BLEAlertSerializer, CloudAlertSerializer

class AccidentReportView(APIView):
    permission_classes = [AllowAny]  # anyone can access

    def get(self, request):
        reports = AccidentReport.objects.all().order_by('-timestamp')
        serializer = AccidentReportSerializer(reports, many=True)
        return Response({"status": True, "reports": serializer.data})

    def post(self, request):
        data = request.data
        serializer = AccidentReportSerializer(data=data)
        if serializer.is_valid():
            # temporarily skip user assignment
            serializer.save(user=None)  
            return Response({"status": True, "report": serializer.data})
        else:
            return Response({"status": False, "errors": serializer.errors})


class VoiceAccidentReportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Receive voice text from app
        voice_text = request.data.get("voice_text", "")
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")

        # Keywords for accident/emergency
        keywords = ["accident", "help", "emergency", "crash", "injury"]
        detected = any(word.lower() in voice_text.lower() for word in keywords)

        if detected:
            # ✅ FIX: Use request.user if authenticated, otherwise None
            user = request.user if request.user.is_authenticated else None
            
            report = AccidentReport.objects.create(
                user=user,
                latitude=latitude,
                longitude=longitude,
                severity="high",
                description=f"Voice detected: {voice_text}",
                reported_via="voice"
            )
            serializer = AccidentReportSerializer(report)
            # Trigger notification here (next step)
            return Response({"status": True, "report": serializer.data})
        else:
            return Response({"status": False, "message": "No emergency detected in voice"})


class SensorAccidentReportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Sensor data from request
        latitude = float(request.data.get("latitude", 0))
        longitude = float(request.data.get("longitude", 0))
        acc_x = float(request.data.get("acc_x", 0))
        acc_y = float(request.data.get("acc_y", 0))
        acc_z = float(request.data.get("acc_z", 0))
        gyro_x = float(request.data.get("gyro_x", 0))
        gyro_y = float(request.data.get("gyro_y", 0))
        gyro_z = float(request.data.get("gyro_z", 0))

        # Use ML model to predict severity
        severity = predict_accident({
            "acc_x": acc_x,
            "acc_y": acc_y,
            "acc_z": acc_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z
        })

        # ✅ FIX: Use request.user if authenticated, otherwise None
        user = request.user if request.user.is_authenticated else None

        # Save accident report
        report = AccidentReport.objects.create(
            user=user,
            latitude=latitude,
            longitude=longitude,
            severity=severity,
            description=f"Sensor data detected accident: acc_x={acc_x}, acc_y={acc_y}, acc_z={acc_z}, gyro_x={gyro_x}, gyro_y={gyro_y}, gyro_z={gyro_z}",
            reported_via="sensor"
        )
        serializer = AccidentReportSerializer(report)
        return Response({"status": True, "report": serializer.data})


# -------------------------------
# BLE Alert Views
# -------------------------------
class BLEAlertView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            latitude = request.data.get("latitude")
            longitude = request.data.get("longitude")
            message = request.data.get("message", "Emergency detected nearby!")
            severity = request.data.get("severity", "unknown")
            location_name = request.data.get("location_name", "")
            broadcast_duration = request.data.get("duration_seconds", 30)

            # ✅ Save BLE alert to database
            alert = BLEAlert.objects.create(
                latitude=latitude,
                longitude=longitude,
                message=message,
                severity=severity,
                location_name=location_name,
                broadcast_duration=broadcast_duration,
                status="broadcast"
            )

            print(f"📡 [BACKEND] BLE Alert Created: {message}")

            return Response({
                "status": True,
                "message": "BLE alert broadcast successfully.",
                "alert_id": str(alert.id),
                "data": BLEAlertSerializer(alert).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ [BACKEND] BLE Alert Error: {e}")
            return Response({
                "status": False,
                "message": f"Failed to create BLE alert: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BLEAlertListView(APIView):
    """View all BLE alerts with filtering"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Get query parameters for filtering
            severity = request.query_params.get('severity')
            status = request.query_params.get('status')
            hours = request.query_params.get('hours', 24)  # Default last 24 hours
            
            alerts = BLEAlert.objects.all()
            
            # Apply filters
            if severity:
                alerts = alerts.filter(severity=severity)
            if status:
                alerts = alerts.filter(status=status)
            if hours:
                time_threshold = timezone.now() - timezone.timedelta(hours=int(hours))
                alerts = alerts.filter(timestamp__gte=time_threshold)
            
            alerts = alerts.order_by('-timestamp')
            serializer = BLEAlertSerializer(alerts, many=True)
            
            # Statistics
            total_count = alerts.count()
            high_severity_count = alerts.filter(severity='high').count()
            medium_severity_count = alerts.filter(severity='medium').count()
            low_severity_count = alerts.filter(severity='low').count()

            return Response({
                "status": True,
                "count": total_count,
                "statistics": {
                    "high_severity": high_severity_count,
                    "medium_severity": medium_severity_count,
                    "low_severity": low_severity_count,
                    "broadcast_status": alerts.filter(status='broadcast').count(),
                    "received_status": alerts.filter(status='received').count(),
                },
                "alerts": serializer.data
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch BLE alerts: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BLEAlertDetailView(APIView):
    """Get specific BLE alert details"""
    permission_classes = [AllowAny]

    def get(self, request, alert_id):
        try:
            alert = BLEAlert.objects.get(id=alert_id)
            serializer = BLEAlertSerializer(alert)
            return Response({
                "status": True,
                "alert": serializer.data
            })
        except BLEAlert.DoesNotExist:
            return Response({
                "status": False,
                "message": "BLE alert not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching BLE alert: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------------
# Cloud Alert Views
# -------------------------------
class CloudAlertView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            device_token = request.data.get("device_token")
            title = request.data.get("title", "Emergency Alert")
            alert_message = request.data.get("body", request.data.get("message", "Emergency alert!"))
            is_emergency = request.data.get("is_emergency", False)
            additional_data = request.data.get("data", {})

            if not device_token:
                return Response({
                    "status": False, 
                    "message": "Missing device_token"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Save Cloud alert to database
            alert = CloudAlert.objects.create(
                device_token=device_token,
                title=title,
                alert_message=alert_message,
                is_emergency=is_emergency,
                data=additional_data,
                status="sent"
            )

            print(f"☁️ [BACKEND] Cloud Alert Created: {title} - {alert_message}")

            # Here you would integrate with actual FCM service
            # For now, we'll simulate successful sending
            
            return Response({
                "status": True,
                "message": "Cloud alert sent successfully.",
                "alert_id": str(alert.id),
                "data": CloudAlertSerializer(alert).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ [BACKEND] Cloud Alert Error: {e}")
            return Response({
                "status": False,
                "message": f"Failed to send cloud alert: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CloudAlertListView(APIView):
    """View all Cloud alerts with filtering"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Get query parameters for filtering
            status = request.query_params.get('status')
            is_emergency = request.query_params.get('is_emergency')
            hours = request.query_params.get('hours', 24)
            
            alerts = CloudAlert.objects.all()
            
            # Apply filters
            if status:
                alerts = alerts.filter(status=status)
            if is_emergency is not None:
                alerts = alerts.filter(is_emergency=is_emergency.lower() == 'true')
            if hours:
                time_threshold = timezone.now() - timezone.timedelta(hours=int(hours))
                alerts = alerts.filter(timestamp__gte=time_threshold)
            
            alerts = alerts.order_by('-timestamp')
            serializer = CloudAlertSerializer(alerts, many=True)
            
            # Statistics
            total_count = alerts.count()
            emergency_count = alerts.filter(is_emergency=True).count()
            sent_count = alerts.filter(status='sent').count()
            delivered_count = alerts.filter(status='delivered').count()
            failed_count = alerts.filter(status='failed').count()

            return Response({
                "status": True,
                "count": total_count,
                "statistics": {
                    "emergency_alerts": emergency_count,
                    "sent": sent_count,
                    "delivered": delivered_count,
                    "failed": failed_count,
                },
                "alerts": serializer.data
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch cloud alerts: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CloudAlertDetailView(APIView):
    """Get specific Cloud alert details"""
    permission_classes = [AllowAny]

    def get(self, request, alert_id):
        try:
            alert = CloudAlert.objects.get(id=alert_id)
            serializer = CloudAlertSerializer(alert)
            return Response({
                "status": True,
                "alert": serializer.data
            })
        except CloudAlert.DoesNotExist:
            return Response({
                "status": False,
                "message": "Cloud alert not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching cloud alert: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlertStatisticsView(APIView):
    """Get overall alert statistics"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Time ranges for statistics
            now = timezone.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            last_24_hours = now - timezone.timedelta(hours=24)
            last_7_days = now - timezone.timedelta(days=7)

            # BLE Alert Statistics
            ble_total = BLEAlert.objects.count()
            ble_today = BLEAlert.objects.filter(timestamp__gte=today).count()
            ble_24h = BLEAlert.objects.filter(timestamp__gte=last_24_hours).count()
            ble_7d = BLEAlert.objects.filter(timestamp__gte=last_7_days).count()

            # Cloud Alert Statistics
            cloud_total = CloudAlert.objects.count()
            cloud_today = CloudAlert.objects.filter(timestamp__gte=today).count()
            cloud_24h = CloudAlert.objects.filter(timestamp__gte=last_24_hours).count()
            cloud_7d = CloudAlert.objects.filter(timestamp__gte=last_7_days).count()

            # Severity breakdown
            high_severity = BLEAlert.objects.filter(severity='high').count()
            medium_severity = BLEAlert.objects.filter(severity='medium').count()
            low_severity = BLEAlert.objects.filter(severity='low').count()

            # Emergency alerts
            emergency_alerts = CloudAlert.objects.filter(is_emergency=True).count()

            return Response({
                "status": True,
                "statistics": {
                    "ble_alerts": {
                        "total": ble_total,
                        "today": ble_today,
                        "last_24_hours": ble_24h,
                        "last_7_days": ble_7d,
                        "severity_breakdown": {
                            "high": high_severity,
                            "medium": medium_severity,
                            "low": low_severity
                        }
                    },
                    "cloud_alerts": {
                        "total": cloud_total,
                        "today": cloud_today,
                        "last_24_hours": cloud_24h,
                        "last_7_days": cloud_7d,
                        "emergency_alerts": emergency_alerts,
                        "status_breakdown": {
                            "sent": CloudAlert.objects.filter(status='sent').count(),
                            "delivered": CloudAlert.objects.filter(status='delivered').count(),
                            "failed": CloudAlert.objects.filter(status='failed').count()
                        }
                    },
                    "total_alerts": ble_total + cloud_total
                }
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error fetching statistics: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@csrf_exempt
def emergency_notify(request):
    """
    API Endpoint: /api/emergency/notify/
    Accepts JSON payload like:
    {
        "latitude": 17.3850,
        "longitude": 78.4867,
        "severity": "high",
        "description": "Severe crash detected",
        "reported_via": "manual"
    }
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))

        latitude = body.get('latitude')
        longitude = body.get('longitude')
        severity = body.get('severity', 'medium')
        description = body.get('description', 'Emergency Alert Triggered')
        reported_via = body.get('reported_via', 'manual')

        if not latitude or not longitude:
            return JsonResponse({"error": "Latitude and longitude required"}, status=400)

        # ✅ FIX: Use request.user if authenticated, otherwise None
        user = request.user if request.user.is_authenticated else None

        report = AccidentReport.objects.create(
            id=uuid.uuid4(),
            user=user,
            latitude=latitude,
            longitude=longitude,
            severity=severity,
            description=description,
            reported_via=reported_via,
            timestamp=timezone.now()
        )

        response_data = {
            "success": True,
            "message": "Emergency alert received successfully!",
            "report": {
                "id": str(report.id),
                "latitude": report.latitude,
                "longitude": report.longitude,
                "severity": report.severity,
                "description": report.description,
                "reported_via": report.reported_via,
                "timestamp": report.timestamp.isoformat(),
            }
        }

        return JsonResponse(response_data, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    User registration endpoint
    """
    try:
        # ✅ FIX: Using the custom User model imported at top
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        phone_number = request.data.get('phone_number', '')  # Optional field from your model

        if not username or not email or not password:
            return Response({
                'status': False,
                'message': 'Username, email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({
                'status': False,
                'message': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({
                'status': False,
                'message': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ FIX: Create user using your custom User model with all required fields
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number or f"+91{username}",  # Default phone number
            is_driver=False,  # Default values for your custom fields
            is_bystander=True
        )

        return Response({
            'status': True,
            'message': 'User registered successfully',
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"❌ [BACKEND] Registration error: {e}")
        return Response({
            'status': False,
            'message': f'Registration failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)