from flask import Flask, request, jsonify
import requests
import base64
import datetime
import config

app = Flask(__name__)

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
