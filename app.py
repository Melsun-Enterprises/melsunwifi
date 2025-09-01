from flask import Flask, request, jsonify, render_template
import requests
import base64
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from config import (
    BUSINESS_SHORTCODE, LNM_PASSKEY, DARJA_API_KEY, CALLBACK_URL,
    EASYPASS_BASE, EASYPASS_API_KEY, PLAN_DURATIONS,
    EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# ------------------ IN-MEMORY STORAGE ------------------
guests_data = {}
scheduler = BackgroundScheduler()
scheduler.start()
scheduled_expirations = {}

# ------------------ EMAIL & SMS HELPERS ------------------
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_sms(phone, message):
    stk_url = f"https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
    payload = {
        "InitiatorName": BUSINESS_SHORTCODE,
        "SecurityCredential": DARJA_API_KEY,
        "CommandID": "BusinessPayment",
        "Amount": 1,
        "PartyA": BUSINESS_SHORTCODE,
        "PartyB": phone,
        "Remarks": message,
        "QueueTimeOutURL": CALLBACK_URL,
        "ResultURL": CALLBACK_URL,
        "Occasion": "Notification"
    }
    headers = {"Authorization": f"Bearer {DARJA_API_KEY}"}
    try:
        requests.post(stk_url, json=payload, headers=headers)
        print(f"SMS sent to {phone}")
    except Exception as e:
        print(f"Failed to send SMS to {phone}: {e}")

# ------------------ M-PESA STK PUSH ------------------
@app.route("/buy_access", methods=["POST"])
def buy_access():
    data = request.json
    phone = data["phone"]
    amount = data["amount"]
    portal_name = data.get("portal_name", "SelfReg")
    voucher_plan = data.get("voucher_plan", "DailyPass")

    # Generate STK password
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{BUSINESS_SHORTCODE}{LNM_PASSKEY}{timestamp}".encode()).decode()

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": f"Access-{portal_name}",
        "TransactionDesc": f"Purchase {voucher_plan}"
    }
    headers = {"Authorization": f"Bearer {DARJA_API_KEY}"}
    response = requests.post(stk_url, json=payload, headers=headers)

    return jsonify({
        "status": "pending",
        "message": "Payment request sent. Please complete payment on your phone.",
        "stk_response": response.json()
    })

# ------------------ PAYMENT CALLBACK ------------------
@app.route("/payment/callback", methods=["POST"])
def payment_callback():
    callback_data = request.json
    try:
        items = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
        phone = next(i["Value"] for i in items if i["Name"] == "PhoneNumber")
        amount = next(i["Value"] for i in items if i["Name"] == "Amount")
    except:
        return jsonify({"status": "error", "message": "Invalid callback data"}), 400

    portal_name = "SelfReg"
    voucher_plan = callback_data.get("plan_name", "DailyPass")
    duration_hours = PLAN_DURATIONS.get(voucher_plan, 24)

    # Generate voucher
    voucher_code = f"{phone}-{amount}"
    voucher_url = f"{EASYPASS_BASE}/{portal_name}/voucher_plans/{voucher_plan}/vouchers/generate"
    requests.put(voucher_url, json={"voucher_codes":[voucher_code], "managed_account":""},
                 headers={"Authorization": f"Bearer {EASYPASS_API_KEY}"})

    # Create guest
    guest_email = f"{phone}@example.com"
    guest_payload = {
        "email": guest_email,
        "first_name": phone,
        "last_name": "User",
        "password": voucher_code,
        "voucher_plan": voucher_plan
    }
    requests.post(f"{EASYPASS_BASE}/{portal_name}/guests", json=guest_payload,
                  headers={"Authorization": f"Bearer {EASYPASS_API_KEY}"})

    # Enable access
    requests.put(f"{EASYPASS_BASE}/{portal_name}/guests/{guest_email}/enable_access",
                 headers={"Authorization": f"Bearer {EASYPASS_API_KEY}"})

    # Store guest info
    guests_data[guest_email] = {
        "email": guest_email,
        "voucher_code": voucher_code,
        "plan": voucher_plan,
        "status": "Active",
        "expires_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
    }

    # Schedule expiration
    def expire_access(email=guest_email):
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        requests.put(f"{EASYPASS_BASE}/{portal_name}/guests/{email}/disable_access", headers=headers)
        requests.put(f"{EASYPASS_BASE}/{portal_name}/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher_code], "managed_account": ""}, headers=headers)
        guests_data[email]["status"] = "Expired"
        send_email(email, "Access Expired", f"Your {voucher_plan} access has expired.")
        print(f"Expired {email}")

    run_time = datetime.now() + timedelta(hours=duration_hours)
    job = scheduler.add_job(expire_access, 'date', run_date=run_time)
    scheduled_expirations[guest_email] = job

    return jsonify({
        "status": "success",
        "voucher_code": voucher_code,
        "voucher_plan": voucher_plan,
        "access": "enabled",
        "expires_at": run_time.isoformat()
    })

# ------------------ DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", guests=list(guests_data.values()))

# ------------------ EXTEND / REVOKE ------------------
@app.route("/extend_access", methods=["POST"])
def extend_access():
    email = request.form.get("email")
    extra_hours = int(request.form.get("extra_hours", 0))

    if email not in guests_data or guests_data[email]["status"] != "Active":
        return "Guest not active or not found", 404

    old_expire = datetime.fromisoformat(guests_data[email]["expires_at"])
    new_expire = old_expire + timedelta(hours=extra_hours)
    guests_data[email]["expires_at"] = new_expire.isoformat()

    old_job = scheduled_expirations.get(email)
    if old_job:
        old_job.remove()

    voucher_code = guests_data[email]["voucher_code"]
    voucher_plan = guests_data[email]["plan"]

    def expire_access(email=email):
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        requests.put(f"{EASYPASS_BASE}/SelfReg/guests/{email}/disable_access", headers=headers)
        requests.put(f"{EASYPASS_BASE}/SelfReg/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher_code], "managed_account": ""}, headers=headers)
        guests_data[email]["status"] = "Expired"
        send_email(email, "Access Expired", f"Your access has expired.")
        print(f"Extended access expired for {email}")

    job = scheduler.add_job(expire_access, 'date', run_date=new_expire)
    scheduled_expirations[email] = job

    send_email(email, "Access Extended", f"Your access has been extended by {extra_hours} hours.")
    return f"Access for {email} extended. New expiry: {new_expire}"

@app.route("/revoke_access", methods=["POST"])
def revoke_access():
    email = request.form.get("email")
    if email not in guests_data or guests_data[email]["status"] != "Active":
        return "Guest not active or not found", 404

    voucher_code = guests_data[email]["voucher_code"]
    voucher_plan = guests_data[email]["plan"]

    headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
    requests.put(f"{EASYPASS_BASE}/SelfReg/guests/{email}/disable_access", headers=headers)
    requests.put(f"{EASYPASS_BASE}/SelfReg/voucher_plans/{voucher_plan}/vouchers/remove",
                 json={"voucher_codes": [voucher_code], "managed_account": ""}, headers=headers)

    old_job = scheduled_expirations.get(email)
    if old_job:
        old_job.remove()
        scheduled_expirations.pop(email, None)

    guests_data[email]["status"] = "Revoked"
    send_email(email, "Access Revoked", f"Your access has been revoked.")
    return f"Access for {email} has been revoked immediately."

@app.route("/guests_data")
def guests_data_api():
    return jsonify(list(guests_data.values()))

# ------------------ RUN APP ------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
