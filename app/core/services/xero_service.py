# api/xero.py
from fastapi import APIRouter, Depends, HTTPException
import xero_python
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token

router = APIRouter()

@router.get("/authorize")
async def authorize_xero(user: User = Depends(get_current_user)):
    config = Configuration(
        oauth2_token=OAuth2Token(
            client_id=settings.XERO_CLIENT_ID,
            client_secret=settings.XERO_CLIENT_SECRET
        )
    )
    api_client = ApiClient(configuration=config)
    
    # Generate authorization URL
    auth_url = f"https://login.xero.com/identity/connect/authorize?response_type=code&client_id={settings.XERO_CLIENT_ID}&redirect_uri={settings.REDIRECT_URI}&scope=offline_access accounting.transactions accounting.contacts"
    
    return {"authorization_url": auth_url}