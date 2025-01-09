# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()

@router.get("/")
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return {"message": "List users endpoint"}

@router.get("/{user_id}")
async def read_user(user_id: int, db: Session = Depends(get_db)):
    return {"message": f"Get user {user_id}"}