from typing import Dict, Optional
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import settings  # Importamos settings desde config

class XeroOAuthService:
    def __init__(self):
        self.client_id = settings.XERO_CLIENT_ID
        self.client_secret = settings.XERO_CLIENT_SECRET
        self.redirect_uri = (
            "http://localhost:8000/auth/callback"
            if settings.ENVIRONMENT == "development"
            else "https://xero.dataextractor.cloud/auth/callback"
        )
        # Scopes necesarios para la aplicación
        self.scope = " ".join([
            "offline_access",          # Para mantener la conexión segura
            "openid profile email",    # Información básica del usuario
            "accounting.reports.read", # Para acceder a Balance Sheet y P&L
            "accounting.contacts",     # Para ver relaciones entre empresas
            "accounting.transactions"  # Para validar transacciones entre empresas
        ])
        self.token_url = "https://identity.xero.com/connect/token"
        self.authorize_url = "https://login.xero.com/identity/connect/authorize"

    def get_authorization_url(self, state: str) -> str:
        """Generate the authorization URL for Xero OAuth flow."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state
        }
        print(f"Redirect URI being used: {self.redirect_uri}")  # Log para debugging
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query_string}"

    def get_permissions_description(self) -> dict:
        """Retorna descripción detallada de los permisos solicitados."""
        return {
            "Balance Sheet": {
                "scope": "accounting.reports.read",
                "endpoint": "/Reports/BalanceSheet",
                "description": "Acceso de solo lectura al Balance General"
            },
            "Profit and Loss": {
                "scope": "accounting.reports.read",
                "endpoint": "/Reports/ProfitAndLoss",
                "description": "Acceso de solo lectura al Estado de Resultados"
            },
            "Contacts": {
                "scope": "accounting.contacts",
                "description": "Ver información de empresas relacionadas"
            },
            "Transactions": {
                "scope": "accounting.transactions",
                "description": "Ver transacciones entre empresas relacionadas"
            }
        }

xero_oauth_service = XeroOAuthService()