# config.py
# M-PESA Daraja API Configuration

MPESA_CONSUMER_KEY = "qb6BMKWaoXeOFXfY2ipBbs7AAhjxAz4B"
MPESA_CONSUMER_SECRET = "dbYlJycxbh8h5af3"
MPESA_PASSKEY = "28b5e3100273dc2a58b269b79bf7724b661f346aba08c0ab2a3851fa37685888"
MPESA_ENV = "sandbox"  # or "production"

# Mpesa Config
SHORTCODE = "4107899"   # Your Paybill / Till Number
CALLBACK_URL = "https://<your-codespaces-url>/mpesa/callback"
# Callback URL (must be publicly accessible, e.g., your Codespaces/Render/Heroku URL)
CALLBACK_URL = "https://<your-public-url>/mpesa/callback"
