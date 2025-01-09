from app.services.xero_client import get_invoices, get_tenants
from app.services.token_manager_db import refresh_access_token

def query_invoice(db, tenant_id, client_id, client_secret):
    """
    Consulta facturas desde Xero usando el refresh token guardado en la base de datos.
    """
    tokens = refresh_access_token(db, tenant_id, client_id, client_secret)
    access_token = tokens['access_token']

    tenants = get_tenants(access_token)
    tenant_id = tenants[0]['tenantId']

    return get_invoices(access_token, tenant_id)
