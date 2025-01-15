import requests, base64
from sqlalchemy.orm import Session
from app.models.models_xero import RefreshToken


def refresh_access_token(db, tenant_id, client_id, client_secret):
    """
    Renueva el access_token usando el refresh_token almacenado en la base de datos.
    """
    refresh_token = load_refresh_token(db, tenant_id)
    print("REFRESH TOKEN de load_refresh_token() ..........", refresh_token)
    if not refresh_token:
        raise Exception("No se encontró un refresh token válido.")

    response = requests.post(
        "https://identity.xero.com/connect/token",
        headers={
            'Authorization': f'Basic {base64.urlsafe_b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
    )
    print("el response >>>>>>>>>> ", response.json())
    if response.status_code == 200:
        tokens = response.json()
        print("VEMOS TOKENS EN refresh_access_token =========>", tokens)
        save_refresh_token(db, tenant_id, tokens['refresh_token'])  # Guarda el nuevo refresh token
        return tokens
    else:
        raise Exception(f"Error al renovar el token: {response.status_code} - {response.text}")

def save_refresh_token(session: Session, tenant_id: str, refresh_token: str):
    """
    Guarda o actualiza el refresh token en la base de datos.
    """
    token_entry = session.query(RefreshToken).filter_by(tenant_id=tenant_id).first()
    if token_entry:
        token_entry.refresh_token = refresh_token
    else:
        token_entry = RefreshToken(tenant_id=tenant_id, refresh_token=refresh_token)
        session.add(token_entry)
    session.commit()

def load_refresh_token(session: Session, tenant_id: str):
    """
    Carga el refresh token desde la base de datos.
    """
    print("[token_manager_db] TENANT ID ====> ", tenant_id)
    token_entry = session.query(RefreshToken).filter_by(tenant_id=tenant_id).first()
    print("TOKEN ENTRY ...................", token_entry.refresh_token)
    return token_entry.refresh_token if token_entry else None