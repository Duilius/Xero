# utils/validators.py
import httpx
from datetime import datetime
from typing import Optional, Dict
from fastapi import HTTPException, Response, logger
from app.services.xero_balance_service import

class AccountValidators:
   @staticmethod
   def validate_period(from_date: str, to_date: str):
       try:
           f_date = datetime.strptime(from_date, "%Y-%m-%d")
           t_date = datetime.strptime(to_date, "%Y-%m-%d")
           if f_date > t_date:
               raise HTTPException(status_code=400, detail="Invalid date range")
       except ValueError:
           raise HTTPException(status_code=400, detail="Invalid date format")

# error_handlers.py
async def handle_xero_error(response: Response) -> Optional[Dict]:
   if response.status_code == 401:
       raise HTTPException(status_code=401, detail="Token expired")
   elif response.status_code == 429:
       raise HTTPException(status_code=429, detail="Rate limit exceeded")
   return None

