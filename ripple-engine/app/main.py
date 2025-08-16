# --- Standard Library Imports ---
import os
import json
import sys # New import to exit gracefully
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import List

# --- Third-Party Imports ---
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlmodel import Session, SQLModel
import stripe

# --- Local Application Imports ---
from . import generator
from . import models
from . import security
from .database import engine

# ===================================================================
# 1. CONFIGURATION & VALIDATION
# ===================================================================

# --- NEW: Explicitly check for environment variables ---
required_secrets = ["STRIPE_SECRET_KEY", "STRIPE_PRICE_ID", "YOUR_DOMAIN", "SECRET_KEY", "GOOGLE_API_KEY"]
missing_secrets = [secret for secret in required_secrets if not os.getenv(secret)]

if missing_secrets:
    print("❌ FATAL ERROR: The following required environment variables are not set:")
    for secret in missing_secrets:
        print(f"  - {secret}")
    print("\nPlease set them in your GitHub repository's Codespaces secrets and reload the window.")
    sys.exit(1) # Exit the application if secrets are missing
# --- END NEW VALIDATION ---

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN")

# ===================================================================
# 2. APP LIFESPAN
# ===================================================================

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Starting up and creating database tables...")
    create_db_and_tables()
    yield
    print("INFO:     Shutting down...")

app = FastAPI(
    title="Ripple API",
    description="An API to generate social media posts from a given text.",
    version="0.5.1", # Version updated for better validation
    lifespan=lifespan
)

# ... (The rest of the file remains exactly the same) ...

# ===================================================================
# 3. DEPENDENCIES AND HELPERS (Unchanged)
# ===================================================================
def get_session():
    with Session(engine) as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.query(models.User).filter(models.User.email == email).first()
    if user is None: raise credentials_exception
    return user

# ===================================================================
# 4. API ENDPOINTS (Unchanged)
# ===================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
    with open(html_file_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/register", response_model=models.UserPublic)
def register_user(user_create: models.UserCreate, session: Session = Depends(get_session)):
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
    return current_user

@app.post("/generate", response_model=dict)
def generate_posts_endpoint(article: models.Article, current_user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.subscription_status == "free":
        pro_platforms = {"Twitter", "LinkedIn", "Pinterest", "Reddit"}
        requested_platforms = set(article.platforms)
        if not requested_platforms.isdisjoint(pro_platforms):
            raise HTTPException(
                status_code=403,
                detail="Upgrade to Pro to generate posts for Twitter, LinkedIn, Pinterest, or Reddit."
            )
    posts = generator.create_ripples(article.text, article.platforms)
    if not posts:
        raise HTTPException(status_code=500, detail="Failed to generate posts from the text.")
    new_generation = models.Generation(
        original_text=article.text,
        generated_posts={"posts": posts},
        selected_platforms=article.platforms,
        owner_id=current_user.id
    )
    session.add(new_generation)
    session.commit()
    return {"status": "success", "posts": posts}

@app.get("/generations", response_model=List[models.Generation])
def get_user_generations(current_user: models.User = Depends(get_current_user)):
    return current_user.generations

@app.post("/create-checkout-session")
def create_checkout_session(current_user: models.User = Depends(get_current_user), session: Session = Depends(get_session)):
    try:
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            session.add(current_user)
            session.commit()
            session.refresh(current_user)
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=f"{YOUR_DOMAIN}?checkout_status=success",
            cancel_url=f"{YOUR_DOMAIN}?checkout_status=cancel",
            metadata={"user_id": current_user.id}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    event = None
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    if event["type"] == 'checkout.session.completed':
        session_data = event["data"]["object"]
        user_id = session_data.get("metadata", {}).get("user_id")
        if user_id:
            with Session(engine) as db_session:
                user = db_session.get(models.User, int(user_id))
                if user:
                    user.subscription_status = "pro"
                    db_session.add(user)
                    db_session.commit()
                    print(f"User {user_id} upgraded to Pro.")
    return {"status": "success"}