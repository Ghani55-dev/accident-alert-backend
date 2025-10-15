from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AccidentReport
from .serializers import AccidentReportSerializer
from .ml_model import predict_accident
import requests
from django.conf import settings

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
            report = AccidentReport.objects.create(
                user=request.user,
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

        # Save accident report
        report = AccidentReport.objects.create(
            user=request.user,
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

        # In real BLE integration, we’ll use Bluetooth broadcasting.
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
