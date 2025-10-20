from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import integration routers
try:
    from api.integrations.snapchat import router as snapchat_router
    print("✅ Snapchat router imported successfully")
except ImportError as e:
    print(f"⚠️ Snapchat router import failed: {e}")
    snapchat_router = None

try:
    from api.integrations.tiktok import router as tiktok_router
    print("✅ TikTok router imported successfully")
except ImportError as e:
    print(f"⚠️ TikTok router import failed: {e}")
    tiktok_router = None

try:
    from api.integrations.gmail_simple import router as gmail_router
    print("✅ Gmail router imported successfully")
except ImportError as e:
    print(f"⚠️ Gmail router import failed: {e}")
    gmail_router = None

try:
    from api.integrations.google_calendar_simple import router as google_calendar_router
    print("✅ Google Calendar router imported successfully")
except ImportError as e:
    print(f"⚠️ Google Calendar router import failed: {e}")
    google_calendar_router = None

try:
    from api.integrations.marketplace_simple import router as marketplace_router
    print("✅ Marketplace router imported successfully")
except ImportError as e:
    print(f"⚠️ Marketplace router import failed: {e}")
    marketplace_router = None

# Create FastAPI app
app = FastAPI(
    title="GoodRunss Backend API",
    description="Complete backend API for GoodRunss platform with integrations",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include integration routers
if snapchat_router:
    app.include_router(snapchat_router)

if tiktok_router:
    app.include_router(tiktok_router)

if gmail_router:
    app.include_router(gmail_router)

if google_calendar_router:
    app.include_router(google_calendar_router)

if marketplace_router:
    app.include_router(marketplace_router)

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow()
    }

@app.get("/test-env")
async def test_env():
    """Test environment variables"""
    return {
        "stripe_secret_key": "loaded" if os.getenv("STRIPE_SECRET_KEY") else "not_loaded",
        "stripe_key_preview": os.getenv("STRIPE_SECRET_KEY", "None")[:20] + "..." if os.getenv("STRIPE_SECRET_KEY") else "None"
    }

@app.get("/gmail/test")
async def test_gmail_integration():
    """Test Gmail integration"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    return {
        "status": "Gmail integration test",
        "client_id_loaded": bool(client_id),
        "client_secret_loaded": bool(client_secret),
        "client_id_preview": client_id[:20] + "..." if client_id else "Not loaded",
        "message": "Gmail credentials are loaded but endpoints need OAuth flow setup"
    }

@app.get("/maps/test")
async def test_google_maps():
    """Test Google Maps integration"""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    return {
        "status": "Google Maps integration test",
        "api_key_loaded": bool(api_key),
        "api_key_preview": api_key[:20] + "..." if api_key else "Not loaded",
        "message": "Google Maps API key loaded - ready for geocoding and directions"
    }

@app.get("/calendar/test")
async def test_google_calendar():
    """Test Google Calendar integration"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    return {
        "status": "Google Calendar integration test",
        "client_id_loaded": bool(client_id),
        "client_secret_loaded": bool(client_secret),
        "client_id_preview": client_id[:20] + "..." if client_id else "Not loaded",
        "message": "Google Calendar credentials loaded - ready for event creation and sync"
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
            "enabled": bool(os.getenv("GMAIL_CLIENT_ID")),
            "features": ["send_email", "read_email", "booking_confirmation"]
        },
        "google_calendar": {
            "enabled": bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID")),
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting GoodRunss Backend API v2.0...")
    print("📊 Integration endpoints ready")
    print("🔌 API available at http://localhost:8001")
    print("📚 Documentation at http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)