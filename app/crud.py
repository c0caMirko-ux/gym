
# app/crud.py
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import User, Session as SessionModel, Reservation, WaitlistEntry, Trainer
from uuid import UUID

def get_user_by_email(db: Session, email: str):
    return db.execute(select(User).filter_by(email=email)).scalar_one_or_none()

def get_session_for_update(db: Session, session_id: UUID):
    return db.execute(select(SessionModel).filter_by(id=session_id).with_for_update()).scalar_one_or_none()

def count_booked(db: Session, session_id: UUID):
    return db.execute(select(func.count()).select_from(Reservation).filter_by(session_id=session_id, status='booked')).scalar_one()
