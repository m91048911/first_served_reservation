from sqlalchemy import Column, Integer, String, Boolean

from database import Base

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)