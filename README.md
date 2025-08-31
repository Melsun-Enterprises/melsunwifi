MelsunWiFi ISP Billing System

A Flask-based ISP billing and voucher management system integrating Safaricom Daraja (M-Pesa) and cnMaestro EasyPass.

Features

M-Pesa STK Push payment integration.

Daraja OAuth token auto-generation.

EasyPass voucher creation and guest access management.

Extend / revoke guest access.

Dashboard to monitor active guests and their expiration.

Email notifications for access expiration and reminders.

Environment Variables / Config (config.py)
# Daraja
BUSINESS_SHORTCODE = "4107899"
LNM_PASSKEY = "28b5e3100273dc2a58b269b79bf7724b661f346aba08c0ab2a3851fa37685888"
CALLBACK_URL = "https://melsunwifi.onrender.com/payment/callback"

# Daraja OAuth (sandbox credentials)
CONSUMER_KEY = "YOUR_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"

# EasyPass
EASYPASS_BASE = "https://YOUR_CNMAESTRO_EASYPASS_URL/api/easypass"
EASYPASS_API_KEY = "YOUR_EASYPASS_API_KEY"
PLAN_DURATIONS = {"DailyPass": 24, "WeeklyPass": 168}  # in hours

# Email (SMTP)
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USER = "your@email.com"
EMAIL_PASS = "your_email_password"

Setup

Clone repo:

git clone https://github.com/YOUR_USERNAME/melsunwifi.git
cd melsunwifi


Create virtual environment:

python3 -m venv venv
source venv/bin/activate


Install requirements:

pip install -r requirements.txt


Configure .env or config.py with your Daraja, EasyPass, and SMTP credentials.

Running Locally
python app.py


Dashboard: http://localhost:5000/dashboard

Guests API: http://localhost:5000/guests_data

Buy Access (STK Push): POST http://localhost:5000/buy_access with JSON:

{
    "phone": "2547XXXXXXXX",
    "amount": 100,
    "voucher_plan": "DailyPass"
}

Deploy on Render

Create a new Web Service.

Connect GitHub repo.

Set Build Command:

pip install -r requirements.txt


Set Start Command:

gunicorn app:app


Add environment variables from config.py under Environment in Render dashboard.

Deploy.

Notes

Make sure EasyPass API key has proper permissions for guest and voucher management.