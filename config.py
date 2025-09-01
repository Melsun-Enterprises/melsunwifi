# config.py

# ---------------- M-PESA / DARJA ----------------
BUSINESS_SHORTCODE = "4107899"
LNM_PASSKEY = "28b5e3100273dc2a58b269b79bf7724b661f346aba08c0ab2a3851fa37685888"

CONSUMER_KEY = "qb6BMKWaoXeOFXfY2ipBbs7AAhjxAz4B"        # From Safaricom Daraja portal
CONSUMER_SECRET = "dbYlJycxbh8h5af3"  # From Safaricom Daraja portal

CALLBACK_URL = "https://melsunwifi.onrender.com/payment/callback"

# ---------------- EASYPASS ----------------
EASYPASS_BASE = "https://eu-w1-s15-qrbwqhor20.cloud.cambiumnetworks.com/easypass"
EASYPASS_API_KEY = "JhOFT9GB2035atY1"
PLAN_DURATIONS = {"DailyPass": 24, "HourlyPass": 1}

# ---------------- EMAIL ----------------
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USER = "you@example.com"
EMAIL_PASS = "your_email_password"
