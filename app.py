from flask import Flask, request, jsonify
import requests
import base64
import datetime
import config

app = Flask(__name__)
from flask import Flask, request, jsonify
import config
from datetime import datetime
import base64
import requests

app = Flask(__name__)

def generate_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(config.CONSUMER_KEY, config.CONSUMER_SECRET))
    return response.json().get("access_token")

def stk_push(phone_number, amount):
    token = generate_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        (config.SHORTCODE + config.PASSKEY + timestamp).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "BusinessShortCode": config.SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": config.SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": config.CALLBACK_URL,
        "AccountReference": "MelsunWiFi",
        "TransactionDesc": "WiFi Payment"
    }

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ---- Routes ----
@app.route("/pay", methods=["POST"])
def pay():
    data = request.get_json()
    phone = data.get("phone")
    amount = data.get("amount")
    res = stk_push(phone, amount)
    return jsonify(res)

@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json()
    print("M-Pesa Callback:", data)
    # later: save to database
    return jsonify({"ResultCode": 0, "ResultDesc": "Callback received successfully"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

# ------------------------------
# 1. Health check
# ------------------------------
@app.route("/")
def home():
    return jsonify({"message": "MelsunWifi Billing API is running 🚀"})


# ------------------------------
# 2. Generate M-Pesa Access Token
# ------------------------------
def get_mpesa_token():
    consumer_key = config.MPESA_CONSUMER_KEY
    consumer_secret = config.MPESA_CONSUMER_SECRET
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    r = requests.get(api_URL, auth=(consumer_key, consumer_secret))
    return r.json()["access_token"]


# ------------------------------
# 3. Lipa na M-Pesa Online Payment (STK Push)
# ------------------------------
@app.route("/pay", methods=["POST"])
def lipa_na_mpesa():
    data = request.json
    phone = data.get("phone")
    amount = data.get("amount", 30)  # default KES 30 for daily WiFi

    token = get_mpesa_token()
    headers = {"Authorization": f"Bearer {token}"}

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        (config.MPESA_SHORTCODE + config.MPESA_PASSKEY + timestamp).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "BusinessShortCode": config.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": config.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/callback",  # update later
        "AccountReference": "MelsunWifi",
        "TransactionDesc": "Melsun Wifi Payment",
    }

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)

    return jsonify(response.json())


# ------------------------------
# 4. cnMaestro Voucher Generation (Mock)
# ------------------------------
@app.route("/voucher", methods=["POST"])
def generate_voucher():
    data = request.json
    plan = data.get("plan", config.DEFAULT_PLAN)

    # ⚠️ Placeholder: normally you'd call cnMaestro API with OAuth2 token here
    voucher_code = "MEL" + datetime.datetime.now().strftime("%H%M%S")

    return jsonify({
        "portal": config.DEFAULT_PORTAL,
        "plan": plan,
        "voucher": voucher_code,
        "status": "generated ✅"
    })


# ------------------------------
# Run app
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
