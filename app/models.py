
# app/models.py
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum, JSON, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid
from datetime import datetime

Base = declarative_base()

class UserRole(str, enum.Enum):
    member = 'member'
    trainer = 'trainer'
    admin = 'admin'

class ReservationStatus(str, enum.Enum):
    booked = 'booked'
    cancelled = 'cancelled'
    attended = 'attended'
    no_show = 'no_show'

class SessionStatus(str, enum.Enum):
    scheduled = 'scheduled'
    cancelled = 'cancelled'
    completed = 'completed'

def gen_uuid():
    return str(uuid.uuid4())

class Plan(Base):
    __tablename__ = 'plans'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    max_monthly_bookings = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.member)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('gym.plans.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    plan = relationship("Plan")
    trainer_profile = relationship("Trainer", uselist=False, back_populates="user")

class Trainer(Base):
    __tablename__ = 'trainers'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('gym.users.id'), nullable=False, unique=True)
    bio = Column(Text)
    specialties = Column(ARRAY(String))
    certifications = Column(ARRAY(String))
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="trainer_profile")

class Location(Base):
    __tablename__ = 'locations'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(Text)
    capacity = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class ClassType(Base):
    __tablename__ = 'class_types'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)
    is_group = Column(Boolean, default=True)
    level = Column(String)
    price_cents = Column(Integer, default=0)
    currency = Column(String, default='USD')
    created_at = Column(DateTime, server_default=func.now())

class Session(Base):
    __tablename__ = 'sessions'
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='ck_session_times'),
        {'schema': 'gym'}
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_type_id = Column(UUID(as_uuid=True), ForeignKey('gym.class_types.id'), nullable=False)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey('gym.trainers.id'))
    location_id = Column(UUID(as_uuid=True), ForeignKey('gym.locations.id'))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, nullable=False, default=20)
    status = Column(SAEnum(SessionStatus), default=SessionStatus.scheduled)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    class_type = relationship("ClassType")
    trainer = relationship("Trainer")
    location = relationship("Location")
    reservations = relationship("Reservation", back_populates="session")

class Reservation(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('gym.sessions.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('gym.users.id'), nullable=False)
    status = Column(SAEnum(ReservationStatus), default=ReservationStatus.booked)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    session = relationship("Session", back_populates="reservations")
    user = relationship("User")

class WaitlistEntry(Base):
    __tablename__ = 'waitlist_entries'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('gym.sessions.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('gym.users.id'), nullable=False)
    position = Column(Integer, nullable=False)
    notified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime, server_default=func.now())
    session = relationship("Session")
    user = relationship("User")

class Payment(Base):
    __tablename__ = 'payments'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('gym.users.id'))
    reservation_id = Column(UUID(as_uuid=True), ForeignKey('gym.reservations.id'))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default='USD')
    provider = Column(String)
    provider_payment_id = Column(String)
    status = Column(String)
    payment_metadata= Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

class TrainerAvailability(Base):
    __tablename__ = 'trainer_availability'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey('gym.trainers.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    recurring_rule = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = {'schema': 'gym'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String)
    entity_id = Column(UUID(as_uuid=True))
    action = Column(String)
    payload = Column(JSON)
    performed_by = Column(UUID(as_uuid=True), ForeignKey('gym.users.id'))
    created_at = Column(DateTime, server_default=func.now())
