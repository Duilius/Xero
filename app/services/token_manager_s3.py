from app.utils.s3_helper import save_refresh_token_to_s3, load_refresh_token_from_s3
import requests
import base64
from config import XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_REDIRECT_URI, XERO_ACCESS_TOKEN, XERO_REFRESH_TOKEN

# Configuración global
REDIRECT_URI = 'https://xero.com'
TOKEN_ENDPOINT = 'https://identity.xero.com/connect/token'

# Credenciales codificadas en base64
b64_id_secret = base64.urlsafe_b64encode(f"{XERO_CLIENT_ID}:{XERO_CLIENT_SECRET}".encode()).decode()


def refresh_access_token():
    refresh_token = load_refresh_token_from_s3()
    if not refresh_token:
        raise Exception("No se encontró un refresh token válido.")

    response = requests.post(
        "https://identity.xero.com/connect/token",
        headers={
            'Authorization': f'Basic {b64_id_secret}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
    )

    if response.status_code == 200:
        tokens = response.json()
        save_refresh_token_to_s3(tokens['refresh_token'])
        return tokens
    else:
        raise Exception(f"Error===> al renovar el token: {response.status_code}")
