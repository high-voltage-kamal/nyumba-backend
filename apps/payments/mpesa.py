"""
payments/mpesa.py
M-Pesa Daraja API integration for Kenya.
Implements STK Push (Lipa Na M-Pesa Online).
"""

import base64
import logging
import requests
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


def get_mpesa_base_url():
    if settings.MPESA_ENV == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def get_access_token():
    url = f"{get_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Basic {encoded}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException as e:
        logger.error(f"M-Pesa token error: {e}")
        return None


def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def stk_push(phone_number, amount, account_ref, description):
    phone = phone_number.replace("+", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    access_token = get_access_token()
    if not access_token:
        return {"error": "Could not connect to M-Pesa. Try again."}

    password, timestamp = generate_password()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": str(account_ref)[:12],
        "TransactionDesc": description[:13],
    }

    url = f"{get_mpesa_base_url()}/mpesa/stkpush/v1/processrequest"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        data = response.json()
        logger.info(f"STK Push response: {data}")

        if data.get("ResponseCode") == "0":
            return {
                "success": True,
                "merchant_request_id": data.get("MerchantRequestID"),
                "checkout_request_id": data.get("CheckoutRequestID"),
                "message": "M-Pesa prompt sent to your phone. Enter your PIN to complete payment.",
            }
        else:
            return {"error": data.get("errorMessage", "M-Pesa request failed.")}

    except requests.RequestException as e:
        logger.error(f"STK Push network error: {e}")
        return {"error": "Network error connecting to M-Pesa."}


def parse_stk_callback(callback_data):
    body = callback_data.get("Body", {}).get("stkCallback", {})
    result_code = body.get("ResultCode")
    checkout_request_id = body.get("CheckoutRequestID")

    if result_code == 0:
        items = body.get("CallbackMetadata", {}).get("Item", [])
        metadata = {item["Name"]: item.get("Value") for item in items}
        return {
            "success": True,
            "checkout_request_id": checkout_request_id,
            "receipt_number": metadata.get("MpesaReceiptNumber"),
            "amount": metadata.get("Amount"),
            "phone": str(metadata.get("PhoneNumber")),
            "transaction_date": str(metadata.get("TransactionDate")),
        }
    else:
        return {
            "success": False,
            "checkout_request_id": checkout_request_id,
            "result_code": result_code,
            "result_desc": body.get("ResultDesc"),
        }
