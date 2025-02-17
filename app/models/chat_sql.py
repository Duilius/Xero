from pydantic import BaseModel
from typing import Optional

class ChatQuery(BaseModel):
    text: str
    user_id: Optional[str] = None
    business_id: Optional[str] = None
    is_data_query: Optional[bool] = False  # Para el checkbox que mencionaste
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Who are my top 5 customers?",
                "user_id": "user123",
                "business_id": "business456",
                "is_data_query": True
            }
        }