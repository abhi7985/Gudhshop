# accounts/api_views.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from twilio.rest import Client
import json

User = get_user_model()
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

@csrf_exempt
def send_otp(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = json.loads(request.body.decode())
    phone = data.get("phone")

    if not phone:
        return JsonResponse({"detail": "phone is required"}, status=400)

    verification = twilio_client.verify.v2.services(
        settings.TWILIO_VERIFY_SERVICE_SID
    ).verifications.create(to=phone, channel="sms")

    return JsonResponse({"success": True, "status": verification.status})


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST required"}, status=405)

    data = json.loads(request.body.decode())
    phone = data.get("phone")
    code = data.get("code")

    if not phone or not code:
        return JsonResponse({"detail": "phone and code are required"}, status=400)

    verification_check = twilio_client.verify.v2.services(
        settings.TWILIO_VERIFY_SERVICE_SID
    ).verification_checks.create(to=phone, code=code)

    if verification_check.status != "approved":
        return JsonResponse({"success": False, "detail": "Invalid code"}, status=400)

    # Get or create user
    user, _ = User.objects.get_or_create(username=phone, defaults={"phone": phone})

    # Example: using DRF TokenAuth; adjust to your auth system
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=user)

    return JsonResponse({"success": True, "token": token.key})
