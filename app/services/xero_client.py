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
