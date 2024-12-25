import requests

def get_tenants(access_token):
    """
    Obtiene la lista de tenants autorizados.
    """
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
    """
    Obtiene las facturas desde Xero.
    """
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
