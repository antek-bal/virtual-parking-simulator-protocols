from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.app.models.base import Base
from datetime import datetime

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(3), nullable=False)
    registration_no = Column(String(10), unique=True, nullable=False)

    active_parking = relationship("ActiveParking", back_populates="vehicle", uselist=False)
    history = relationship("ParkingHistory", back_populates="vehicle")


class ActiveParking(Base):
    __tablename__ = "active_parking"

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), primary_key=True)
    entry_time = Column(DateTime, default=datetime.now, nullable=False)
    floor = Column(Integer, nullable=False)
    spot_number = Column(Integer, nullable=False)
    is_paid = Column(Boolean, default=False)
    payment_time = Column(DateTime, nullable=True)
    paid_fee = Column(Float, nullable=True)

    vehicle = relationship("Vehicle", back_populates="active_parking")

    __table_args__ = (CheckConstraint('floor >= 0 AND floor <= 4', name='check_floor_range'),)


class ParkingHistory(Base):
    __tablename__ = "parking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, default=datetime.now, nullable=False)
    floor = Column(Integer, nullable=False)
    fee = Column(Float, nullable=False)

    vehicle = relationship("Vehicle", back_populates="history")