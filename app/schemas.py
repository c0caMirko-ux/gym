
# app/schemas.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class RegisterIn(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SessionOut(BaseModel):
    id: UUID
    class_type_id: UUID
    trainer_id: Optional[UUID]
    location_id: Optional[UUID]
    start_time: datetime
    end_time: datetime
    capacity: int
    status: str

class ReserveIn(BaseModel):
    session_id: UUID
    auto_waitlist: bool = True
