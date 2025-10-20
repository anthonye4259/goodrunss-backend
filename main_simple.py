"""
Simplified GoodRunss Backend API - No Database Dependencies
Focuses on API endpoints without complex database relationships
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import OAuth router
try:
    from api.integrations.oauth import router as oauth_router
    print("✅ OAuth router imported successfully")
except ImportError as e:
    print(f"⚠️ OAuth router import failed: {e}")
    oauth_router = None

# Import Wearables Demo router
try:
    from api.integrations.wearables_demo import router as wearables_demo_router
    print("✅ Wearables Demo router imported successfully")
except ImportError as e:
    print(f"⚠️ Wearables Demo router import failed: {e}")
    wearables_demo_router = None

# Import HealthKit router
try:
    from api.integrations.healthkit import router as healthkit_router
    print("✅ HealthKit router imported successfully")
except ImportError as e:
    print(f"⚠️ HealthKit router import failed: {e}")
    healthkit_router = None

# Create FastAPI app
app = FastAPI(
    title="GoodRunss Backend API",
    description="Complete backend API for GoodRunss platform with integrations",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include OAuth router
if oauth_router:
    app.include_router(oauth_router)

# Include Wearables Demo router
if wearables_demo_router:
    app.include_router(wearables_demo_router)

# Include HealthKit router
if healthkit_router:
    app.include_router(healthkit_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "GoodRunss Backend API v2.0",
        "status": "active",
        "integrations": [
            "Stripe Payments",
            "Achievements & Viral Moments", 
            "Wearable Devices (Apple Watch, Whoop)",
            "Gmail Integration",
            "Google Calendar",
            "Twilio SMS",
            "Instagram Social Sharing",
            "Google Maps",
            "Zoom Virtual Sessions",
            "Snapchat Integration",
            "TikTok Integration"
        ],
        "docs": "/docs",
        "timestamp": datetime.utcnow()
    }

@app.get("/integrations/status")
async def get_integrations_status():
    """Get status of all integrations"""
    return {
        "stripe": {
            "enabled": bool(os.getenv("STRIPE_SECRET_KEY")),
            "features": ["payments", "connect", "instant_payouts"]
        },
        "achievements": {
            "enabled": True,
            "features": ["viral_moments", "social_sharing", "leaderboards"]
        },
        "wearables": {
            "enabled": True,
            "supported_devices": ["apple_watch", "whoop", "fitbit"]
        },
        "gmail": {
            "enabled": bool(os.getenv("GOOGLE_CLIENT_ID")),
            "features": ["send_email", "read_email", "booking_confirmation"]
        },
        "google_calendar": {
            "enabled": bool(os.getenv("GOOGLE_CLIENT_ID")),
            "features": ["create_events", "sync_bookings", "get_events"]
        },
        "twilio_sms": {
            "enabled": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "features": ["send_sms", "2fa", "booking_reminders"]
        },
        "instagram": {
            "enabled": bool(os.getenv("INSTAGRAM_APP_ID")),
            "features": ["post_achievements", "social_sharing"]
        },
        "google_maps": {
            "enabled": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
            "features": ["directions", "nearby_courts", "geocoding"]
        },
        "zoom": {
            "enabled": bool(os.getenv("ZOOM_API_KEY")),
            "features": ["virtual_sessions", "meeting_creation"]
        },
        "snapchat": {
            "enabled": bool(os.getenv("SNAPCHAT_APP_ID")),
            "features": ["login", "stories_sharing", "bitmoji", "creative_kit"]
        },
        "tiktok": {
            "enabled": bool(os.getenv("TIKTOK_CLIENT_KEY")),
            "features": ["login", "video_sharing", "viral_moments", "analytics", "trending_hashtags"]
        }
    }

# Marketplace endpoints
@app.get("/marketplace/listings")
async def get_marketplace_listings():
    """Get marketplace listings"""
    sample_listings = [
        {
            "id": 1,
            "title": "Wilson Basketball - Like New",
            "description": "Official NBA game ball, barely used.",
            "price": 25.00,
            "type": "sell",
            "condition": "Like New",
            "category": "basketball",
            "seller": "Mike Johnson",
            "distance": "0.5 miles",
            "image": "/basketball-action.png",
            "zip_code": "10001",
            "is_available": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": 2,
            "title": "Tennis Racket - Wilson Pro Staff",
            "description": "High-performance racket, great for intermediate players.",
            "price": 15.00,
            "type": "rent",
            "rental_period": "per day",
            "condition": "Good",
            "category": "tennis",
            "seller": "Sarah Chen",
            "distance": "1.2 miles",
            "image": "/tennis-racket.png",
            "zip_code": "10001",
            "is_available": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    return {
        "listings": sample_listings,
        "total": len(sample_listings),
        "success": True
    }

@app.get("/marketplace/listings/{listing_id}")
async def get_listing(listing_id: int):
    """Get a specific marketplace listing"""
    return {
        "id": listing_id,
        "title": "Wilson Basketball - Like New",
        "description": "Official NBA game ball, barely used.",
        "price": 25.00,
        "type": "sell",
        "condition": "Like New",
        "category": "basketball",
        "seller": "Mike Johnson",
        "distance": "0.5 miles",
        "image": "/basketball-action.png",
        "zip_code": "10001",
        "is_available": True,
        "created_at": datetime.utcnow().isoformat()
    }

# Gmail endpoints
@app.get("/gmail/auth-url")
async def get_gmail_auth_url():
    """Get Gmail OAuth URL"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return {"error": "Google API credentials not configured"}
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8001/auth/google/callback&scope=https://www.googleapis.com/auth/gmail.send&response_type=code"
    return {"auth_url": auth_url}

# Google Calendar endpoints
@app.get("/calendar/auth-url")
async def get_calendar_auth_url():
    """Get Google Calendar OAuth URL"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return {"error": "Google API credentials not configured"}
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8001/auth/google/callback&scope=https://www.googleapis.com/auth/calendar&response_type=code"
    return {"auth_url": auth_url}

# Snapchat endpoints
@app.get("/snapchat/auth-url")
async def get_snapchat_auth_url():
    """Get Snapchat OAuth URL"""
    app_id = os.getenv("SNAPCHAT_APP_ID")
    if not app_id:
        return {"error": "Snapchat API credentials not configured"}
    
    auth_url = f"https://accounts.snapchat.com/login/oauth2/authorize?client_id={app_id}&redirect_uri=http://localhost:3000/auth/snapchat/callback&response_type=code&scope=user.display_name,user.bitmoji.avatar"
    return {"auth_url": auth_url}

# TikTok endpoints
@app.get("/tiktok/auth-url")
async def get_tiktok_auth_url():
    """Get TikTok OAuth URL"""
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    if not client_key:
        return {"error": "TikTok API credentials not configured"}
    
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?client_key={client_key}&scope=user.info.basic,video.publish&response_type=code&redirect_uri=http://localhost:3000/auth/tiktok/callback"
    return {"auth_url": auth_url}

# Stripe endpoints
@app.get("/payments/status")
async def get_payments_status():
    """Get Stripe payments status"""
    stripe_enabled = bool(os.getenv("STRIPE_SECRET_KEY"))
    return {
        "stripe_enabled": stripe_enabled,
        "features": ["payments", "connect", "instant_payouts"] if stripe_enabled else []
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting GoodRunss Backend API v2.0...")
    print("📊 Integration endpoints ready")
    print("🔌 API available at http://localhost:8001")
    print("📚 Documentation at http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)

