from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
verify = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID)

def send_otp(phone):
    """
    phone must be in E.164 format, e.g. +9198xxxxxx12
    """
    verify.verifications.create(to=phone, channel='sms')

def check_otp(phone, code):
    try:
        result = verify.verification_checks.create(to=phone, code=code)
    except TwilioRestException:
        return False
    return result.status == 'approved'
