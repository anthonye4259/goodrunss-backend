"""
Marketplace Integration - SIMPLIFIED WITHOUT DATABASE DEPENDENCY ISSUES
Uses direct database connection
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles"""
    R = 3959
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return round(R * c, 1)

def get_db_connection():
    """Get direct database connection"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./goodrunss.db")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def seed_sample_data():
    """Seed database with sample listings if empty"""
    try:
        from models import MarketplaceListing
        db = get_db_connection()
        
        existing = db.query(MarketplaceListing).first()
        if existing:
            db.close()
            return
        
        sample_listings = [
            MarketplaceListing(
                title="Wilson Basketball - Like New",
                description="Official size basketball, barely used",
                price=25, type="sell", condition="Like New", category="basketball",
                seller_id=1, seller_name="Mike Johnson", seller_rating=4.8,
                zip_code="10001", latitude=40.7506, longitude=-73.9971,
                image="/basketball-action.png", is_available=True
            ),
            MarketplaceListing(
                title="Tennis Racket - Wilson Pro Staff",
                description="Professional tennis racket",
                price=15, type="rent", rental_period="per day", condition="Good",
                category="tennis", seller_id=1, seller_name="Sarah Chen",
                seller_rating=4.9, zip_code="10001", latitude=40.7489,
                longitude=-73.9680, image="/tennis-racket.png", is_available=True
            ),
            MarketplaceListing(
                title="Pickleball Paddle Set",
                description="Two paddles and balls",
                price=40, type="sell", condition="Excellent", category="pickleball",
                seller_id=1, seller_name="David Lee", seller_rating=4.7,
                zip_code="10002", latitude=40.7157, longitude=-73.9866,
                image="/pickleball-paddle.jpg", is_available=True
            ),
            MarketplaceListing(
                title="Golf Club Set - Callaway",
                description="Complete set with bag",
                price=50, type="rent", rental_period="per week", condition="Good",
                category="golf", seller_id=1, seller_name="Emma Wilson",
                seller_rating=4.6, zip_code="10003", latitude=40.7316,
                longitude=-73.9894, image="/assorted-golf-clubs.png", is_available=True
            ),
            MarketplaceListing(
                title="Basketball Shoes - Nike Size 10",
                description="High-top shoes, worn twice",
                price=60, type="sell", condition="Like New", category="basketball",
                seller_id=1, seller_name="James Brown", seller_rating=4.9,
                zip_code="10001", latitude=40.7580, longitude=-73.9855,
                image="/athletic-basketball-shoes.png", is_available=True
            ),
            MarketplaceListing(
                title="Volleyball Net & Ball",
                description="Portable net with ball",
                price=20, type="rent", rental_period="per day", condition="Good",
                category="volleyball", seller_id=1, seller_name="Lisa Martinez",
                seller_rating=4.8, zip_code="10002", latitude=40.7209,
                longitude=-73.9876, image="/volleyball-net.jpg", is_available=True
            )
        ]
        
        for listing in sample_listings:
            db.add(listing)
        db.commit()
        db.close()
        print("✅ Seeded 6 marketplace listings")
    except Exception as e:
        print(f"⚠️ Seed failed: {e}")

@router.get("/listings")
async def get_marketplace_listings(
    zip_code: Optional[str] = None,
    type: Optional[str] = "all",
    category: Optional[str] = None,
    search: Optional[str] = None,
    user_lat: Optional[float] = 40.7489,
    user_lon: Optional[float] = -73.9680
):
    """Get marketplace listings from DATABASE"""
    try:
        from models import MarketplaceListing
        db = get_db_connection()
        
        # Seed if empty
        seed_sample_data()
        
        # Query
        query = db.query(MarketplaceListing).filter(MarketplaceListing.is_available == True)
        
        if type and type != "all":
            query = query.filter(MarketplaceListing.type == type)
        if category:
            query = query.filter(MarketplaceListing.category == category)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (MarketplaceListing.title.ilike(search_filter)) |
                (MarketplaceListing.description.ilike(search_filter))
            )
        if zip_code:
            zip_prefix = zip_code[:3]
            query = query.filter(MarketplaceListing.zip_code.like(f"{zip_prefix}%"))
        
        listings = query.order_by(MarketplaceListing.created_at.desc()).all()
        
        # Convert to dict
        result_listings = []
        for listing in listings:
            listing_dict = {
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "type": listing.type,
                "condition": listing.condition,
                "category": listing.category,
                "seller_id": listing.seller_id,
                "seller_name": listing.seller_name,
                "seller_rating": listing.seller_rating,
                "zip_code": listing.zip_code,
                "latitude": listing.latitude,
                "longitude": listing.longitude,
                "image": listing.image,
                "created_at": listing.created_at.isoformat() if listing.created_at else None,
                "is_available": listing.is_available
            }
            
            if listing.rental_period:
                listing_dict["rental_period"] = listing.rental_period
            
            if listing.latitude and listing.longitude:
                distance = calculate_distance(user_lat, user_lon, listing.latitude, listing.longitude)
                listing_dict["distance"] = f"{distance} miles"
                listing_dict["distance_value"] = distance
            else:
                listing_dict["distance"] = "Unknown"
                listing_dict["distance_value"] = 9999
            
            result_listings.append(listing_dict)
        
        result_listings.sort(key=lambda x: x["distance_value"])
        db.close()
        
        return {
            "success": True,
            "count": len(result_listings),
            "listings": result_listings,
            "source": "database"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "listings": []
        }

@router.get("/listings/{listing_id}")
async def get_listing_detail(listing_id: int):
    """Get listing detail from DATABASE"""
    try:
        from models import MarketplaceListing
        db = get_db_connection()
        listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
        db.close()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return {
            "success": True,
            "listing": {
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "type": listing.type,
                "rental_period": listing.rental_period,
                "condition": listing.condition,
                "category": listing.category,
                "seller_name": listing.seller_name,
                "zip_code": listing.zip_code,
                "image": listing.image
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/listings")
async def create_listing(
    title: str, description: str, price: float, type: str,
    condition: str, category: str, zip_code: str, seller_id: int,
    rental_period: Optional[str] = None, image: Optional[str] = None
):
    """Create new listing in DATABASE"""
    try:
        from models import MarketplaceListing
        db = get_db_connection()
        
        new_listing = MarketplaceListing(
            title=title, description=description, price=price, type=type,
            condition=condition, category=category, seller_id=seller_id,
            seller_name="User", seller_rating=5.0, zip_code=zip_code,
            latitude=40.7489, longitude=-73.9680, image=image or "/placeholder.png",
            rental_period=rental_period, is_available=True
        )
        
        db.add(new_listing)
        db.commit()
        db.refresh(new_listing)
        listing_id = new_listing.id
        db.close()
        
        return {
            "success": True,
            "message": "Listing created in database",
            "listing_id": listing_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

