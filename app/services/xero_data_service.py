import httpx
from typing import Optional, Dict

async def get_chart_of_accounts(tenant_id: str, access_token: str) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Reports/BalanceSheet",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                }
            )
            print(f"Balance Sheet response: {response.text}")
            return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error in get_chart_of_accounts: {str(e)}")
        return None