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
# BLE Alert View
# -------------------------------
class BLEAlertView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # BLE alert request from user
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")
        message = request.data.get("message", "Emergency detected nearby!")

        # In real BLE integration, we'll use Bluetooth broadcasting.
        # For now, just simulate response.
        return Response({
            "status": True,
            "message": "BLE alert broadcast simulated successfully.",
            "data": {
                "latitude": latitude,
                "longitude": longitude,
                "alert_message": message
            }
        })


# -------------------------------
# Cloud Alert View (Firebase)
# -------------------------------
class CloudAlertView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Dummy FCM send logic
        device_token = request.data.get("device_token")
        alert_message = request.data.get("message", "Emergency alert!")

        if not device_token:
            return Response({"status": False, "message": "Missing device_token"})

        # Simulate Firebase push
        # (Later replace with actual FCM server key logic)
        return Response({
            "status": True,
            "message": "Cloud alert sent successfully.",
            "to_device": device_token,
            "alert_message": alert_message
        })


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