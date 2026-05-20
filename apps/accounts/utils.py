"""
accounts/utils.py

Utility functions for sending SMS via Africa's Talking API.
Africa's Talking is the go-to SMS provider for Kenya — supports M-Pesa and all Safaricom/Airtel/Telkom.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone_number: str, otp: str) -> bool:
    """
    Send OTP via Africa's Talking SMS API.
    Returns True if sent successfully, False otherwise.

    Africa's Talking docs: https://developers.africastalking.com/docs/sms/sending
    """
    if settings.DEBUG and not settings.AT_API_KEY:
        # In development without API key, just log the OTP
        logger.info(f"[DEV MODE] OTP for {phone_number}: {otp}")
        return True

    url = "https://api.africastalking.com/version1/messaging"
    headers = {
        "apiKey": settings.AT_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    message = f"Your NyumbaDirectly verification code is: {otp}. Expires in 10 minutes. Do not share."
    payload = {
        "username": settings.AT_USERNAME,
        "to": phone_number,
        "message": message,
        "from": settings.AT_SENDER_ID,
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        recipients = data.get("SMSMessageData", {}).get("Recipients", [])
        if recipients and recipients[0].get("status") == "Success":
            logger.info(f"OTP SMS sent to {phone_number}")
            return True
        else:
            logger.error(f"Africa's Talking SMS failed: {data}")
            return False
    except requests.RequestException as e:
        logger.error(f"SMS send error for {phone_number}: {e}")
        return False


def send_whatsapp_notification(phone_number: str, message: str) -> bool:
    """
    Send WhatsApp message via Africa's Talking.
    Used for listing confirmation, verification updates, etc.
    """
    if settings.DEBUG and not settings.AT_API_KEY:
        logger.info(f"[DEV MODE] WhatsApp to {phone_number}: {message}")
        return True

    url = "https://chat.africastalking.com/whatsapp/message"
    headers = {
        "apiKey": settings.AT_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "username": settings.AT_USERNAME,
        "productName": "NyumbaDirectly",
        "to": phone_number,
        "message": {"body": {"type": "text", "text": message}},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"WhatsApp sent to {phone_number}")
        return True
    except requests.RequestException as e:
        logger.error(f"WhatsApp send error for {phone_number}: {e}")
        return False
