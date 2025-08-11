# --- Standard Library Imports ---
import os
from contextlib import asynccontextmanager
from datetime import timedelta

# --- Third-Party Imports ---
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlmodel import Session, SQLModel

# --- Local Application Imports ---
from . import generator
from . import models
from . import security
from .database import engine

# ===================================================================
# 1. DATABASE AND APP LIFESPAN CONFIGURATION
# ===================================================================

def create_db_and_tables():
    """Creates all database tables defined by SQLModel models."""
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    On startup, it creates the database and tables.
    """
    print("INFO:     Starting up and creating database tables...")
    create_db_and_tables()
    yield
    print("INFO:     Shutting down...")

app = FastAPI(
    title="Ripple API",
    description="An API to generate social media posts from a given text.",
    version="0.2.0",
    lifespan=lifespan
)

# ===================================================================
# 2. DEPENDENCIES AND HELPERS
# ===================================================================

def get_session():
    """Dependency to get a database session for a single request."""
    with Session(engine) as session:
        yield session

# OAuth2 scheme definition: tells FastAPI where to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Dependency to decode a JWT and fetch the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# ===================================================================
# 3. API ENDPOINTS
# ===================================================================

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main frontend HTML file."""
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
    with open(html_file_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/register", response_model=models.UserPublic)
def register_user(user_create: models.UserCreate, session: Session = Depends(get_session)):
    """Registers a new user with a hashed password."""
    existing_user = session.query(models.User).filter(models.User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    hashed_password = security.hash_password(user_create.password)
    db_user = models.User(email=user_create.email, hashed_password=hashed_password)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """Logs in a user and returns a JWT access token."""
    user = session.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=models.UserPublic)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """(Protected) Fetches details for the currently logged-in user."""
    return current_user

@app.post("/generate", response_model=dict)
def generate_posts_endpoint(article: models.Article, current_user: models.User = Depends(get_current_user)):
    """(Protected) Receives an article and returns generated social media posts."""
    # Note: current_user is now available here if you want to log usage, etc.
    posts = generator.create_ripples(article.text)
    
    if posts:
        return {"status": "success", "posts": posts}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate posts from the text.")