from token_manager import refresh_access_token
from xero_client import get_invoices, get_tenants

def query_invoice():
    # Renueva el access_token usando el refresh_token almacenado
    tokens = refresh_access_token()
    access_token = tokens['access_token']

    # Obtén el tenant ID
    tenants = get_tenants(access_token)
    tenant_id = tenants[0]['tenantId']  # Usa el primer tenant

    # Consulta facturas
    #invoices = get_invoices(access_token, tenant_id)
    return get_invoices(access_token, tenant_id)
    #print("Facturas obtenidas:", invoices)

"""if __name__ == "__main__":
    query_invoice()"""
