"""
Marketplace Integration - Buy, Sell, Rent Sports Gear
NOW WITH REAL DATABASE INTEGRATION!
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

# Database imports
try:
    from ...database import get_db
    from ...models import MarketplaceListing, User
except ImportError:
    get_db = None
    MarketplaceListing = None
    User = None

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles using Haversine formula"""
    R = 3959  # Earth's radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return round(distance, 1)

def seed_sample_data(db: Session):
    """Seed database with sample listings if empty"""
    existing = db.query(MarketplaceListing).first()
    if existing:
        return  # Already have data
    
    sample_listings = [
        MarketplaceListing(
            title="Wilson Basketball - Like New",
            description="Official size basketball, barely used",
            price=25,
            type="sell",
            condition="Like New",
            category="basketball",
            seller_id=1,
            seller_name="Mike Johnson",
            seller_rating=4.8,
            zip_code="10001",
            latitude=40.7506,
            longitude=-73.9971,
            image="/basketball-action.png",
            is_available=True
        ),
        MarketplaceListing(
            title="Tennis Racket - Wilson Pro Staff",
            description="Professional tennis racket, great condition",
            price=15,
            type="rent",
            rental_period="per day",
            condition="Good",
            category="tennis",
            seller_id=1,
            seller_name="Sarah Chen",
            seller_rating=4.9,
            zip_code="10001",
            latitude=40.7489,
            longitude=-73.9680,
            image="/tennis-racket.png",
            is_available=True
        ),
        MarketplaceListing(
            title="Pickleball Paddle Set",
            description="Two paddles and balls included",
            price=40,
            type="sell",
            condition="Excellent",
            category="pickleball",
            seller_id=1,
            seller_name="David Lee",
            seller_rating=4.7,
            zip_code="10002",
            latitude=40.7157,
            longitude=-73.9866,
            image="/pickleball-paddle.jpg",
            is_available=True
        ),
        MarketplaceListing(
            title="Golf Club Set - Callaway",
            description="Complete set with bag",
            price=50,
            type="rent",
            rental_period="per week",
            condition="Good",
            category="golf",
            seller_id=1,
            seller_name="Emma Wilson",
            seller_rating=4.6,
            zip_code="10003",
            latitude=40.7316,
            longitude=-73.9894,
            image="/assorted-golf-clubs.png",
            is_available=True
        ),
        MarketplaceListing(
            title="Basketball Shoes - Nike Size 10",
            description="High-top basketball shoes, worn twice",
            price=60,
            type="sell",
            condition="Like New",
            category="basketball",
            seller_id=1,
            seller_name="James Brown",
            seller_rating=4.9,
            zip_code="10001",
            latitude=40.7580,
            longitude=-73.9855,
            image="/athletic-basketball-shoes.png",
            is_available=True
        ),
        MarketplaceListing(
            title="Volleyball Net & Ball",
            description="Portable net with official volleyball",
            price=20,
            type="rent",
            rental_period="per day",
            condition="Good",
            category="volleyball",
            seller_id=1,
            seller_name="Lisa Martinez",
            seller_rating=4.8,
            zip_code="10002",
            latitude=40.7209,
            longitude=-73.9876,
            image="/volleyball-net.jpg",
            is_available=True
        )
    ]
    
    for listing in sample_listings:
        db.add(listing)
    db.commit()
    print("✅ Seeded 6 sample marketplace listings")

@router.get("/listings")
async def get_marketplace_listings(
    zip_code: Optional[str] = None,
    type: Optional[str] = "all",
    category: Optional[str] = None,
    search: Optional[str] = None,
    user_lat: Optional[float] = 40.7489,
    user_lon: Optional[float] = -73.9680,
    db: Session = Depends(get_db)
):
    """
    Get marketplace listings with optional filters - NOW FROM DATABASE!
    
    - **zip_code**: Filter by zip code (partial match)
    - **type**: Filter by listing type (all, sell, rent)
    - **category**: Filter by category (basketball, tennis, etc.)
    - **search**: Search in title and description
    - **user_lat**: User latitude for distance calculation
    - **user_lon**: User longitude for distance calculation
    """
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Seed sample data if database is empty
    seed_sample_data(db)
    
    # Start with base query
    query = db.query(MarketplaceListing).filter(MarketplaceListing.is_available == True)
    
    # Filter by type
    if type and type != "all":
        query = query.filter(MarketplaceListing.type == type)
    
    # Filter by category
    if category:
        query = query.filter(MarketplaceListing.category == category)
    
    # Search in title and description
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (MarketplaceListing.title.ilike(search_filter)) |
            (MarketplaceListing.description.ilike(search_filter))
        )
    
    # Filter by zip code (partial match for first 3 digits)
    if zip_code:
        zip_prefix = zip_code[:3]
        query = query.filter(MarketplaceListing.zip_code.like(f"{zip_prefix}%"))
    
    # Execute query
    listings = query.order_by(MarketplaceListing.created_at.desc()).all()
    
    # Convert to dict and calculate distances
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
        
        # Calculate distance
        if listing.latitude and listing.longitude:
            distance = calculate_distance(
                user_lat, user_lon,
                listing.latitude, listing.longitude
            )
            listing_dict["distance"] = f"{distance} miles"
            listing_dict["distance_value"] = distance
        else:
            listing_dict["distance"] = "Unknown"
            listing_dict["distance_value"] = 9999
        
        result_listings.append(listing_dict)
    
    # Sort by distance
    result_listings.sort(key=lambda x: x["distance_value"])
    
    return {
        "success": True,
        "count": len(result_listings),
        "listings": result_listings,
        "source": "database"
    }

@router.get("/listings/{listing_id}")
async def get_listing_detail(listing_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific listing FROM DATABASE"""
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    
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
    }

@router.post("/listings")
async def create_listing(
    title: str,
    description: str,
    price: float,
    type: str,
    condition: str,
    category: str,
    zip_code: str,
    seller_id: int,
    rental_period: Optional[str] = None,
    image: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Create a new marketplace listing IN DATABASE"""
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    new_listing = MarketplaceListing(
        title=title,
        description=description,
        price=price,
        type=type,
        condition=condition,
        category=category,
        seller_id=seller_id,
        seller_name="User",  # Would come from authenticated user
        seller_rating=5.0,
        zip_code=zip_code,
        latitude=latitude or 40.7489,
        longitude=longitude or -73.9680,
        image=image or "/placeholder.png",
        rental_period=rental_period,
        is_available=True
    )
    
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    return {
        "success": True,
        "message": "Listing created successfully in database",
        "listing_id": new_listing.id
    }

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all available categories FROM DATABASE"""
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    categories = db.query(MarketplaceListing.category).distinct().all()
    categories_list = [cat[0] for cat in categories]
    
    return {
        "success": True,
        "categories": categories_list
    }

@router.get("/user/{user_id}/listings")
async def get_user_listings(user_id: int, db: Session = Depends(get_db)):
    """Get all listings for a specific user FROM DATABASE"""
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    listings = db.query(MarketplaceListing).filter(
        MarketplaceListing.seller_id == user_id,
        MarketplaceListing.is_available == True
    ).all()
    
    result_listings = []
    for listing in listings:
        result_listings.append({
            "id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "type": listing.type,
            "condition": listing.condition,
            "category": listing.category,
            "created_at": listing.created_at.isoformat() if listing.created_at else None
        })
    
    return {
        "success": True,
        "count": len(result_listings),
        "listings": result_listings
    }

@router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete a marketplace listing FROM DATABASE (only by owner)"""
    if not get_db:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.seller_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
    
    # Soft delete
    listing.is_available = False
    db.commit()
    
    return {
        "success": True,
        "message": "Listing deleted successfully from database"
    }
