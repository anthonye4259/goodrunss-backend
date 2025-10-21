from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
import httpx
import os
from urllib.parse import urlencode
import secrets
import json
from datetime import datetime, timedelta

router = APIRouter(prefix="/whoop", tags=["Whoop Integration"])

# Whoop API configuration
WHOOP_BASE_URL = "https://api.prod.whoop.com"
WHOOP_AUTH_URL = f"{WHOOP_BASE_URL}/oauth/oauth2"
WHOOP_TOKEN_URL = f"{WHOOP_BASE_URL}/oauth/oauth2/token"

# OAuth state storage (in production, use Redis or database)
oauth_states = {}

@router.get("/credentials")
async def get_whoop_credentials():
    """Get Whoop OAuth credentials"""
    return {
        "client_id": os.getenv("WHOOP_CLIENT_ID"),
        "client_secret": os.getenv("WHOOP_CLIENT_SECRET"), 
        "redirect_uri": os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8001/whoop/callback"),
        "auth_url": WHOOP_AUTH_URL,
    }

@router.get("/login")
async def whoop_login():
    """Start Whoop OAuth flow"""
    client_id = os.getenv("WHOOP_CLIENT_ID")
    redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8001/whoop/callback")
    
    if not client_id:
        raise HTTPException(
            status_code=400, 
            detail="Whoop credentials not configured. Please add WHOOP_CLIENT_ID to .env"
        )
    
    # Generate state for security
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "created_at": datetime.now(),
        "used": False
    }
    
    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:recovery read:workout read:sleep read:cycle",
        "state": state,
    }
    
    auth_url = f"{WHOOP_AUTH_URL}?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Open this URL in your browser to authorize Whoop"
    }

@router.post("/callback")
async def whoop_callback(code: str, state: str):
    """Handle Whoop OAuth callback"""
    client_id = os.getenv("WHOOP_CLIENT_ID")
    client_secret = os.getenv("WHOOP_CLIENT_SECRET")
    redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8001/whoop/callback")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Whoop credentials not configured"
        )
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    if oauth_states[state]["used"]:
        raise HTTPException(status_code=400, detail="State already used")
    
    # Mark state as used
    oauth_states[state]["used"] = True
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                WHOOP_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token exchange failed: {token_response.text}"
                )
            
            token_data = token_response.json()
            
            # Get user info
            user_response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/user/profile/basic",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            
            user_data = user_response.json() if user_response.status_code == 200 else {}
            
            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in"),
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "message": "Whoop OAuth successful!"
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")

@router.get("/user/{user_id}")
async def get_whoop_user_data(user_id: int, access_token: str = Query(...)):
    """Get Whoop user data"""
    try:
        async with httpx.AsyncClient() as client:
            # Get user profile
            profile_response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/user/profile/basic",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if profile_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get user profile: {profile_response.text}"
                )
            
            profile_data = profile_response.json()
            
            return {
                "user_id": user_id,
                "whoop_profile": profile_data,
                "timestamp": datetime.now().isoformat(),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@router.get("/recovery/{user_id}")
async def get_whoop_recovery(user_id: int, access_token: str = Query(...)):
    """Get Whoop recovery data"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/recovery",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get recovery data: {response.text}"
                )
            
            recovery_data = response.json()
            
            return {
                "user_id": user_id,
                "recovery": recovery_data,
                "timestamp": datetime.now().isoformat(),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@router.get("/workouts/{user_id}")
async def get_whoop_workouts(
    user_id: int, 
    access_token: str = Query(...),
    days: int = Query(7, description="Number of days to fetch")
):
    """Get Whoop workout data"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/activity/workout",
                params={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get workout data: {response.text}"
                )
            
            workout_data = response.json()
            
            return {
                "user_id": user_id,
                "workouts": workout_data,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "timestamp": datetime.now().isoformat(),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@router.get("/sleep/{user_id}")
async def get_whoop_sleep(
    user_id: int,
    access_token: str = Query(...),
    days: int = Query(7, description="Number of days to fetch")
):
    """Get Whoop sleep data"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/activity/sleep",
                params={
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get sleep data: {response.text}"
                )
            
            sleep_data = response.json()
            
            return {
                "user_id": user_id,
                "sleep": sleep_data,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "timestamp": datetime.now().isoformat(),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@router.get("/cycle/{user_id}")
async def get_whoop_cycle(user_id: int, access_token: str = Query(...)):
    """Get Whoop cycle data (strain, recovery, sleep)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WHOOP_BASE_URL}/developer/v1/cycle",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get cycle data: {response.text}"
                )
            
            cycle_data = response.json()
            
            return {
                "user_id": user_id,
                "cycle": cycle_data,
                "timestamp": datetime.now().isoformat(),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@router.get("/status/{user_id}")
async def whoop_status(user_id: int):
    """Check Whoop integration status"""
    return {
        "user_id": user_id,
        "integration": "whoop",
        "status": "ready",
        "endpoints": {
            "login": "/whoop/login",
            "callback": "/whoop/callback",
            "recovery": "/whoop/recovery/{user_id}",
            "workouts": "/whoop/workouts/{user_id}",
            "sleep": "/whoop/sleep/{user_id}",
            "cycle": "/whoop/cycle/{user_id}",
        },
        "credentials_configured": bool(os.getenv("WHOOP_CLIENT_ID")),
        "timestamp": datetime.now().isoformat(),
    }

