from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from datetime import datetime

# ---------- Users ----------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)
    role: Literal["admin", "customer"]

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    hashed_password: str
    role: Literal["admin", "customer"]


# ---------- Complaints ----------
class Customer(BaseModel):
    name: str
    email: EmailStr
    phone: str

class ComplaintCreate(BaseModel):
    # Keep the same contract you used earlier: client sends the customer object
    title: str
    description: str
    customer: Customer

class Complaint(BaseModel):
    id: int
    title: str
    description: str
    status: Literal["open", "closed"] = "open"
    customer: Customer
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)





