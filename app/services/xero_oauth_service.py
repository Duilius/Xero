from typing import Dict, List
import httpx
from fastapi import HTTPException
from app.core.config import settings

class XeroOAuthService:
    def __init__(self):
        self.client_id = settings.XERO_CLIENT_ID
        self.client_secret = settings.XERO_CLIENT_SECRET
        self.redirect_uri = (
            "http://localhost:8000/auth/callback"
            if settings.ENVIRONMENT == "development"
            else "https://xero.dataextractor.cloud/auth/callback"
        )
        self.scope = " ".join([
            "offline_access",          
            "openid profile email",    
            "accounting.reports.read", 
            "accounting.contacts",     
            "accounting.transactions"  
        ])
        self.token_url = "https://identity.xero.com/connect/token"
        self.authorize_url = "https://login.xero.com/identity/connect/authorize"

    def get_authorization_url(self, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state
        }
        print(f"Redirect URI being used: {self.redirect_uri}")
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorize_url}?{query_string}"

    async def exchange_code_for_tokens(self, code: str) -> Dict:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to exchange code for tokens: {response.text}")
            return response.json()
        
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Xero."""
        userinfo_url = "https://identity.xero.com/connect/userinfo"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user info from Xero"
                )
                
            return response.json()

    async def get_tenant_connections(self, access_token: str) -> List[Dict]:
        """Get all tenant connections from Xero."""
        connections_url = "https://api.xero.com/connections"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                connections_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get tenant connections"
                )
                
            return response.json()
    
xero_oauth_service = XeroOAuthService()