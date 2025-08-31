# ---------------------------
# EasyPass / Daraja Config
# ---------------------------

# M-Pesa / Daraja
BUSINESS_SHORTCODE = "4107899"                     # Your Paybill / Till Number
LNM_PASSKEY = "28b5e3100273dc2a58b269b79bf7724b661f346aba08c0ab2a3851fa37685888"  # Daraja LNM Passkey
DARJA_API_KEY = "YOUR_DARAJA_ACCESS_TOKEN"        # Replace with your access token
CALLBACK_URL = "https://melsunwifi.onrender.com/payment/callback"

# EasyPass
EASYPASS_BASE = "https://your-cnmaestro-instance/api/easypass"  # Base URL of your EasyPass API
EASYPASS_API_KEY = "YOUR_EASYPASS_API_KEY"                     # Your EasyPass API Key

# Voucher Plan durations in hours
PLAN_DURATIONS = {
    "DailyPass": 24,
    "WeeklyPass": 168,
    "MonthlyPass": 720
}

# Email Config
EMAIL_HOST = "smtp.gmail.com"     # Example: Gmail SMTP
EMAIL_PORT = 587
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_email_password"
