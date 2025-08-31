import os

# Daraja (M-Pesa) config
DARJA_API_KEY = os.environ.get("DARJA_API_KEY", "sandbox_key")
BUSINESS_SHORTCODE = os.environ.get("BUSINESS_SHORTCODE", "4107899")
CALLBACK_URL = os.environ.get("CALLBACK_URL", "https://yourapp.com/payment/callback")

# EasyPass config
EASYPASS_BASE = os.environ.get("EASYPASS_BASE", "https://cnmaestro/api/v1/easypass")
EASYPASS_API_KEY = os.environ.get("EASYPASS_API_KEY", "easy_pass_key")

# Voucher plan durations in hours
PLAN_DURATIONS = {
    "HourlyPass": 1,
    "DailyPass": 24,
    "WeeklyPass": 168
}
# Email notifications
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USER = os.environ.get("EMAIL_USER", "your_email@gmail.com")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "your_email_password")
