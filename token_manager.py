import requests
import base64
from token_storage import save_refresh_token, load_refresh_token
from config import XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_REDIRECT_URI, XERO_ACCESS_TOKEN, XERO_REFRESH_TOKEN

# Configuración global
REDIRECT_URI = 'https://xero.com'
TOKEN_ENDPOINT = 'https://identity.xero.com/connect/token'

# Credenciales codificadas en base64
b64_id_secret = base64.urlsafe_b64encode(f"{XERO_CLIENT_ID}:{XERO_CLIENT_SECRET}".encode()).decode()

def refresh_access_token():
    """
    Renueva el access_token usando el refresh_token guardado.
    """
    refresh_token = load_refresh_token()  # Cargar el refresh_token actual
    if not refresh_token:
        raise Exception("No se encontró un refresh token válido. Debes autorizar la aplicación nuevamente.")

    response = requests.post(
        TOKEN_ENDPOINT,
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
        save_refresh_token(tokens['refresh_token'])  # Guardar el nuevo refresh_token
        return tokens
    else:
        print(f"Error al renovar el token: {response.status_code} - {response.text}")
        raise Exception("No se pudo renovar el access_token.")
