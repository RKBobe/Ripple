from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    
    # We can add default values for tracking creation time
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

# (Keep the existing User class at the top of the file)

# Pydantic model for creating a new user (receives plain password)
class UserCreate(SQLModel):
    email: str
    password: str

# Pydantic model for reading user data (never includes password)
class UserPublic(SQLModel):
    id: int
    email: str
    created_at: datetime