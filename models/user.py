from sqlalchemy import Column, Integer, String

from database import Base

# user table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    password_hash = Column(String, nullable=False)