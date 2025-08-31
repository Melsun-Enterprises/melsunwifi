from flask import Flask, request, jsonify
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from config import DARJA_API_KEY, BUSINESS_SHORTCODE, CALLBACK_URL, EASYPASS_BASE, EASYPASS_API_KEY, PLAN_DURATIONS

app = Flask(__name__)
from flask import Flask, request, jsonify, render_template
# ... other imports ...

# Store guest info in memory (or use Postgres for persistence)
guests_data = {}

@app.route("/payment/callback", methods=["POST"])
def payment_callback():
    # ... existing code ...

    # Store guest info for dashboard
    guests_data[guest_email] = {
        "email": guest_email,
        "voucher_code": voucher_code,
        "plan": voucher_plan,
        "status": "Active",
        "expires_at": run_time.isoformat()
    }

    # Update expiration function to change status
    def expire_access(email=guest_email, portal=portal_name, voucher=voucher_code):
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        requests.put(f"{EASYPASS_BASE}/{portal}/guests/{email}/disable_access", headers=headers)
        requests.put(f"{EASYPASS_BASE}/{portal}/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher], "managed_account": ""}, headers=headers)
        # Update dashboard data
        guests_data[email]["status"] = "Expired"
        print(f"Expired {email} and removed voucher {voucher}")

    # ... scheduling code ...

    return jsonify({...})

# Dashboard route
@app.route("/dashboard")
def dashboard():
    # Pass guest info to template
    return render_template("dashboard.html", guests=list(guests_data.values()))

scheduler = BackgroundScheduler()
scheduler.start()
scheduled_expirations = {}

# Step 1: Initiate M-Pesa payment
@app.route("/buy_access", methods=["POST"])
def buy_access():
    data = request.json
    phone = data["phone"]
    amount = data["amount"]
    portal_name = data.get("portal_name", "SelfReg")
    voucher_plan = data.get("voucher_plan", "DailyPass")

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": "generated_password",
        "Timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
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
    return jsonify(response.json())

# Step 2: Handle Daraja callback
@app.route("/payment/callback", methods=["POST"])
def payment_callback():
    callback_data = request.json
    items = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
    phone = next(i["Value"] for i in items if i["Name"] == "PhoneNumber")
    amount = next(i["Value"] for i in items if i["Name"] == "Amount")
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
    guest_url = f"{EASYPASS_BASE}/{portal_name}/guests"
    guest_payload = {
        "email": guest_email,
        "first_name": phone,
        "last_name": "User",
        "password": voucher_code,
        "voucher_plan": voucher_plan
    }
    guest_resp = requests.post(guest_url, json=guest_payload, headers={"Authorization": f"Bearer {EASYPASS_API_KEY}"})

    # Enable access
    enable_url = f"{EASYPASS_BASE}/{portal_name}/guests/{guest_email}/enable_access"
    requests.put(enable_url, headers={"Authorization": f"Bearer {EASYPASS_API_KEY}"})

    # Schedule expiration based on plan duration
    def expire_access(email=guest_email, portal=portal_name, voucher=voucher_code):
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        # Disable guest
        requests.put(f"{EASYPASS_BASE}/{portal}/guests/{email}/disable_access", headers=headers)
        # Remove voucher
        requests.put(f"{EASYPASS_BASE}/{portal}/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher], "managed_account": ""}, headers=headers)
        print(f"Expired {email} and removed voucher {voucher}")

    run_time = datetime.now() + timedelta(hours=duration_hours)
    job = scheduler.add_job(expire_access, 'date', run_date=run_time)
    scheduled_expirations[guest_email] = job

    return jsonify({
        "status": "success",
        "voucher_code": voucher_code,
        "voucher_plan": voucher_plan,
        "guest_creation": guest_resp.json(),
        "access": "enabled",
        "expires_at": run_time.isoformat()
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
@app.route("/extend_access", methods=["POST"])
def extend_access():
    email = request.form.get("email")
    extra_hours = int(request.form.get("extra_hours", 0))

    if email not in guests_data or guests_data[email]["status"] != "Active":
        return "Guest not active or not found", 404

    # Update expiration time
    old_expire = datetime.fromisoformat(guests_data[email]["expires_at"])
    new_expire = old_expire + timedelta(hours=extra_hours)
    guests_data[email]["expires_at"] = new_expire.isoformat()

    # Cancel existing scheduled job and reschedule
    old_job = scheduled_expirations.get(email)
    if old_job:
        old_job.remove()

    voucher_code = guests_data[email]["voucher_code"]
    voucher_plan = guests_data[email]["plan"]
    portal_name = "SelfReg"

    def expire_access(email=email, portal=portal_name, voucher=voucher_code):
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        # Disable guest access
        requests.put(f"{EASYPASS_BASE}/{portal}/guests/{email}/disable_access", headers=headers)
        # Remove voucher
        requests.put(f"{EASYPASS_BASE}/{portal}/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher], "managed_account": ""}, headers=headers)
        guests_data[email]["status"] = "Expired"
        print(f"Extended access expired for {email} and removed voucher {voucher}")

    # Reschedule expiration
    job = scheduler.add_job(expire_access, 'date', run_date=new_expire)
    scheduled_expirations[email] = job

    return f"Access for {email} extended by {extra_hours} hours. New expiry: {new_expire}"
@app.route("/revoke_access", methods=["POST"])
def revoke_access():
    email = request.form.get("email")

    if email not in guests_data or guests_data[email]["status"] != "Active":
        return "Guest not active or not found", 404

    voucher_code = guests_data[email]["voucher_code"]
    voucher_plan = guests_data[email]["plan"]
    portal_name = "SelfReg"

    headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}

    # Disable guest access immediately
    requests.put(f"{EASYPASS_BASE}/{portal_name}/guests/{email}/disable_access", headers=headers)

    # Remove voucher
    requests.put(f"{EASYPASS_BASE}/{portal_name}/voucher_plans/{voucher_plan}/vouchers/remove",
                 json={"voucher_codes": [voucher_code], "managed_account": ""}, headers=headers)

    # Cancel scheduled expiration job
    old_job = scheduled_expirations.get(email)
    if old_job:
        old_job.remove()
        scheduled_expirations.pop(email, None)

    # Update guest data
    guests_data[email]["status"] = "Revoked"

    return f"Access for {email} has been revoked immediately."
@app.route("/guests_data")
def guests_data_api():
    return jsonify(list(guests_data.values()))
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# Optional: send SMS via Daraja
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
from datetime import timedelta

def schedule_expiration(email, portal_name, voucher_code, voucher_plan, duration_hours):
    # Schedule actual expiration
    expire_time = datetime.now() + timedelta(hours=duration_hours)
    def expire_access():
        headers = {"Authorization": f"Bearer {EASYPASS_API_KEY}"}
        requests.put(f"{EASYPASS_BASE}/{portal_name}/guests/{email}/disable_access", headers=headers)
        requests.put(f"{EASYPASS_BASE}/{portal_name}/voucher_plans/{voucher_plan}/vouchers/remove",
                     json={"voucher_codes": [voucher_code], "managed_account": ""}, headers=headers)
        guests_data[email]["status"] = "Expired"
        send_email(email, "Access Expired", f"Your access has expired for {voucher_plan}.")
        print(f"Expired {email} and removed voucher {voucher_code}")

    job = scheduler.add_job(expire_access, 'date', run_date=expire_time)
    scheduled_expirations[email] = job

    # Schedule reminder 1 hour before
    reminder_time = expire_time - timedelta(hours=1)
    def reminder():
        send_email(email, "Access Expiring Soon", f"Your access will expire in 1 hour for {voucher_plan}.")
        print(f"Reminder sent to {email}")

    scheduler.add_job(reminder, 'date', run_date=reminder_time)
send_email(email, "Access Extended", f"Your access for {voucher_plan} has been extended by {extra_hours} hours. New expiry: {new_expire}.")
send_email(email, "Access Revoked", f"Your access for {voucher_plan} has been revoked by the admin.")
