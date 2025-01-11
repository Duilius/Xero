import httpx
from typing import Optional, Dict

async def get_chart_of_accounts(tenant_id: str, access_token: str) -> Optional[Dict]:
    """Get chart of accounts to identify intercompany accounts structure"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Accounts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                print(f"Error getting accounts: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            return response.json()
            
    except Exception as e:
        print(f"Error in get_chart_of_accounts: {str(e)}")
        return None