from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List

# ===================================================================
# 1. GENERATION MODEL
#    This table stores the history of generated posts.
# ===================================================================
class Generation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    original_text: str
    generated_posts: dict = Field(sa_column=Column(JSON))
    selected_platforms: List[str] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Foreign key to link to the User table
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # Relationship to access the User object from a Generation instance
    owner: "User" = Relationship(back_populates="generations")

# ===================================================================
# 2. USER MODEL
#    Updated to include monetization and subscription fields.
# ===================================================================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # --- NEW MONETIZATION FIELDS ---
    stripe_customer_id: Optional[str] = Field(default=None, index=True)
    subscription_status: str = Field(default="free") # e.g., "free", "pro", "canceled"
    usage_count: int = Field(default=0)
    # --- END NEW FIELDS ---

    # Relationship to access all generations for a user (e.g., my_user.generations)
    generations: List["Generation"] = Relationship(back_populates="owner")

# ===================================================================
# 3. API-SPECIFIC MODELS (Pydantic models)
#    These define the shape of data for API requests and responses.
# ===================================================================

class UserCreate(SQLModel):
    email: str
    password: str

class UserPublic(SQLModel):
    id: int
    email: str
    created_at: datetime

class Article(SQLModel):
    text: str
    platforms: List[str]