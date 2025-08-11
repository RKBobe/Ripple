from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from .database import engine
from sqlmodel import Session
from fastapi import Depends, HTTPException
from . import models
from . import security

# Import our generator function
from . import generator

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Creating database and tables...")
    create_db_and_tables()
    yield
    # Code to run on shutdown (if any)
    print("Shutting down...")

# Initialize the FastAPI app
app = FastAPI(
    title="Ripple API",
    description="An API to generate social media posts from a given text.",
    version="0.1.0",
    lifespan=lifespan
)

# Define the data model for our request body using Pydantic.
# This ensures the incoming data is in the correct format.
class Article(BaseModel):
    text: str
    
# Define a "health check" endpoint for the root URL
from fastapi.responses import HTMLResponse
import os

# Define an endpoint to serve our main HTML file
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Construct the path to the HTML file relative to the app directory
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
    with open(html_file_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Define the main endpoint for generating posts
@app.post("/generate")
def generate_posts_endpoint(article: Article):
    """
    Receives an article text and returns generated social media posts.
    """
    # Call our generator function with the text from the request
    posts = generator.create_ripples(article.text)
    
    if posts:
        return {"status": "success", "posts": posts}
    else:
        # If the generator fails, return an error message.
        return {"status": "error", "message": "Failed to generate posts."}
# (This function will be a dependency that provides a DB session per request)
def get_session():
    with Session(engine) as session:
        yield session

@app.post("/register", response_model=models.UserPublic)
def register_user(user_create: models.UserCreate, session: Session = Depends(get_session)):
    """
    Register a new user.
    """
    # Check if user with this email already exists
    existing_user = session.query(models.User).filter(models.User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=409, # 409 Conflict
            detail="An account with this email already exists.",
        )

    # Hash the password before storing
    hashed_password = security.hash_password(user_create.password)

    # Create a new User instance for the database
    db_user = models.User(
        email=user_create.email, 
        hashed_password=hashed_password
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user