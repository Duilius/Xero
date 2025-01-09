# app/api/xero.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()

@router.get("/connect")
async def connect_xero(db: Session = Depends(get_db)):
    return {"message": "Connect to Xero endpoint"}

@router.get("/callback")
async def xero_callback(code: str, db: Session = Depends(get_db)):
    return {"message": "Xero OAuth callback endpoint"}

@router.get("/tokens/{tenant_id}")
async def get_tokens(tenant_id: str, db: Session = Depends(get_db)):
    return {"message": f"Get tokens for tenant {tenant_id}"}