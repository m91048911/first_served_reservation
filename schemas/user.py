
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name : str
    age : int
    password : str = Field(min_length=8)

class UserUpdate(BaseModel):
    name : str
    age : int

class UserResponse(BaseModel):
    id : int
    name : str
    age : int

class UserLogin(BaseModel):
    name : str
    password: str