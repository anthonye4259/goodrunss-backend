"""
OAuth Authentication Integration
Handles Google and Apple OAuth flows
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import httpx
import jwt
from datetime import datetime, timedelta

# Database imports with fallback
try:
    from ...database import get_db
    from ...models import User
except ImportError:
    get_db = None
    User = None

router = APIRouter(prefix="/oauth", tags=["oauth"])

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/oauth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")

APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
APPLE_CLIENT_SECRET = os.getenv("APPLE_CLIENT_SECRET")
APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI", "http://localhost:8001/oauth/apple/callback")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "goodrunss_super_secret_jwt_key_12345_very_long_and_secure_abcdef")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ============================================================================
# GOOGLE OAUTH
# ============================================================================

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth flow"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Google OAuth 2.0 authorization endpoint
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid email profile&"
        "access_type=offline&"
        "prompt=consent"
    )
    
    return {"authorization_url": auth_url}

@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info from Google
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_info_response.json()
    
    # Extract user data
    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    # Create or get user from database (simplified - no DB for now)
    db = None
    if False:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create new user
            user = User(
                email=email,
                username=email.split("@")[0],
                full_name=name,
                oauth_provider="google",
                oauth_id=google_id,
                profile_picture=picture,
                is_verified=True  # Google-verified email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user with Google info
            user.oauth_provider = "google"
            user.oauth_id = google_id
            if not user.profile_picture:
                user.profile_picture = picture
            db.commit()
        
        user_id = user.id
    else:
        # Fallback if database not configured
        user_id = 1
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": email, "user_id": user_id, "name": name}
    )
    
    # Redirect to frontend with token
    redirect_url = f"{FRONTEND_URL}/mobile/player?token={jwt_token}"
    return RedirectResponse(url=redirect_url)

# ============================================================================
# APPLE OAUTH
# ============================================================================

@router.get("/apple/login")
async def apple_login():
    """Initiate Apple OAuth flow"""
    if not APPLE_CLIENT_ID:
        # Return demo response if Apple not configured
        return {
            "message": "Apple OAuth not configured yet",
            "instructions": "Get Apple Developer account at https://developer.apple.com/",
            "demo_mode": True
        }
    
    # Apple OAuth authorization endpoint
    auth_url = (
        "https://appleid.apple.com/auth/authorize?"
        f"client_id={APPLE_CLIENT_ID}&"
        f"redirect_uri={APPLE_REDIRECT_URI}&"
        "response_type=code id_token&"
        "scope=name email&"
        "response_mode=form_post"
    )
    
    return {"authorization_url": auth_url}

@router.post("/apple/callback")
async def apple_callback(code: str, id_token: str, user: Optional[str] = None):
    """Handle Apple OAuth callback"""
    if not APPLE_CLIENT_ID or not APPLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Apple OAuth not configured")
    
    # Decode the id_token to get user info
    # Note: In production, you should verify the token signature
    try:
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        apple_id = decoded.get("sub")
        email = decoded.get("email")
        
        # Parse user info if provided (only on first login)
        name = None
        if user:
            import json
            user_data = json.loads(user)
            name = f"{user_data.get('name', {}).get('firstName', '')} {user_data.get('name', {}).get('lastName', '')}"
        
        # Create or get user from database (simplified - no DB for now)
        db = None
        if False:
            user_obj = db.query(User).filter(User.email == email).first()
            if not user_obj:
                # Create new user
                user_obj = User(
                    email=email,
                    username=email.split("@")[0] if email else f"apple_{apple_id}",
                    full_name=name,
                    oauth_provider="apple",
                    oauth_id=apple_id,
                    is_verified=True  # Apple-verified email
                )
                db.add(user_obj)
                db.commit()
                db.refresh(user_obj)
            else:
                # Update existing user with Apple info
                user_obj.oauth_provider = "apple"
                user_obj.oauth_id = apple_id
                db.commit()
            
            user_id = user_obj.id
        else:
            # Fallback if database not configured
            user_id = 1
        
        # Create JWT token
        jwt_token = create_access_token(
            data={"sub": email or apple_id, "user_id": user_id, "name": name}
        )
        
        # Redirect to frontend with token
        redirect_url = f"{FRONTEND_URL}/mobile/player?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process Apple login: {str(e)}")

# ============================================================================
# EMAIL/PASSWORD AUTHENTICATION
# ============================================================================

from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(user_data: UserRegister):
    """Register new user with email/password"""
    db = None
    if not db or not User:
        # For now, return a demo token (database not required)
        jwt_token = create_access_token(
            data={"sub": user_data.email, "user_id": 1, "name": user_data.full_name}
        )
        return {
            "message": "Registration successful (demo mode)",
            "token": jwt_token,
            "user": {
                "id": 1,
                "email": user_data.email,
                "name": user_data.full_name
            }
        }
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password (in production, use proper password hashing like bcrypt)
    import hashlib
    hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.email.split("@")[0],
        full_name=user_data.full_name,
        password_hash=hashed_password,
        oauth_provider="email",
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id, "name": new_user.full_name}
    )
    
    return {
        "message": "Registration successful",
        "token": jwt_token,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.full_name
        }
    }

@router.post("/login")
async def login(credentials: UserLogin):
    """Login with email/password"""
    db = None
    if not db or not User:
        # For now, return a demo token (database not required)
        jwt_token = create_access_token(
            data={"sub": credentials.email, "user_id": 1, "name": "Demo User"}
        )
        return {
            "message": "Login successful (demo mode)",
            "token": jwt_token,
            "user": {
                "id": 1,
                "email": credentials.email,
                "name": "Demo User"
            }
        }
    
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    import hashlib
    hashed_password = hashlib.sha256(credentials.password.encode()).hexdigest()
    if user.password_hash != hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    jwt_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "name": user.full_name}
    )
    
    return {
        "message": "Login successful",
        "token": jwt_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name
        }
    }

# ============================================================================
# TOKEN VERIFICATION
# ============================================================================

@router.get("/verify")
async def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("sub"),
            "name": payload.get("name")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

