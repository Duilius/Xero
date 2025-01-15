"""
XeroClient es un cliente mínimo que:

1. Proporciona métodos stub para interactuar con Xero
2. Retorna datos de prueba por ahora
3. Se puede expandir más tarde con la funcionalidad real
"""

from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import requests
from app.services.token_manager_db import refresh_access_token


def query_invoice(db, tenant_id, client_id, client_secret):
    """
    Consulta facturas desde Xero usando el refresh token guardado en la base de datos.
    """
    print("Tenant ID ...................", tenant_id)
    print("CLIENT SECRET ...................", client_secret)
    print("CLIENT ID ...................", client_id)
    tokens = refresh_access_token(db, tenant_id, client_id, client_secret)
    print("TOKENs ========>", tokens)
    access_token = tokens['access_token']


    tenants = get_tenants(access_token)
    tenant_id = tenants[0]['tenantId'] # Usa el primer tenant

    print("TENANT ID ========>", tenant_id)

    # Consulta facturas desde Xero
    return get_invoices(access_token, tenant_id)

def get_tenants(access_token):
    response = requests.get(
        'https://api.xero.com/connections',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
    )
    response.raise_for_status()
    return response.json()

def get_invoices(access_token, tenant_id):
    response = requests.get(
        'https://api.xero.com/api.xro/2.0/Invoices',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Xero-tenant-id': tenant_id,
            'Accept': 'application/json',
        }
    )
    response.raise_for_status()
    return response.json()


class XeroClient:
    def __init__(self):
        """Inicializar cliente de Xero."""
        pass  # Por ahora vacío, luego agregaremos configuración

    async def get_organization_data(self, tenant_id: str, access_token: str) -> Dict:
        """
        Obtener datos de préstamos intercompañía de Xero.
        Por ahora retorna datos de prueba basados en organizaciones reales.
        """
        # TODO: Implementar llamada real a Xero API
        return {
            "transaction_count": 2,
            "total_amount": Decimal("84520.00"),
            "transactions": [
                {
                    "from_org": "Company A",
                    "to_org": "Company B",
                    "amount": Decimal("50000.00"),
                    "status": "active",
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                },
                {
                    "from_org": "Company B",
                    "to_org": "Company C",
                    "amount": Decimal("34520.00"),
                    "status": "pending",
                    "date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
                }
            ]
        }

    async def apply_adjustment(
        self,
        tenant_id: str,
        access_token: str,
        amount: Decimal,
        description: str
    ) -> bool:
        """
        Aplicar un ajuste en Xero.
        Por ahora solo simula la operación.
        """
        # TODO: Implementar llamada real a Xero API
        return True