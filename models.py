"""
Complete Database Models for GoodRunss Backend
Includes all original models plus new integration models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Original Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    is_trainer = Column(Boolean, default=False)
    is_facility_owner = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Location fields
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    
    # Stripe Connect for trainers
    stripe_connect_id = Column(String)
    
    # Social Media Integrations
    snapchat_id = Column(String)
    snapchat_access_token = Column(Text)
    tiktok_id = Column(String)
    tiktok_access_token = Column(Text)
    
    # Relationships - specify exact foreign keys to avoid ambiguity
    bookings = relationship("Booking", back_populates="user", foreign_keys="[Booking.user_id]")
    trainer_bookings = relationship("Booking", back_populates="trainer", foreign_keys="[Booking.trainer_id]")
    courts = relationship("Court", back_populates="owner")
    games = relationship("Game", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    wearable_connections = relationship("UserWearableConnection", back_populates="user")
    email_integrations = relationship("EmailIntegration", back_populates="user")
    calendar_integrations = relationship("CalendarIntegration", back_populates="user")
    social_integrations = relationship("SocialIntegration", back_populates="user")
    zoom_integrations = relationship("ZoomIntegration", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    virtual_sessions = relationship("VirtualSession", back_populates="user")
    marketplace_listings = relationship("MarketplaceListing", back_populates="seller")

class Court(Base):
    __tablename__ = "courts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="courts")
    bookings = relationship("Booking", back_populates="court")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    court_id = Column(Integer, ForeignKey("courts.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, cancelled, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bookings", foreign_keys=[user_id])
    trainer = relationship("User", back_populates="trainer_bookings", foreign_keys=[trainer_id])
    court = relationship("Court", back_populates="bookings")
    transactions = relationship("Transaction", back_populates="booking")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    court_id = Column(Integer, ForeignKey("courts.id"))
    score = Column(Integer, nullable=False)
    duration_minutes = Column(Integer)
    game_type = Column(String)  # pickup, training, tournament
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="games")
    court = relationship("Court")

# New Integration Models

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    trainer_amount = Column(Float, nullable=False)
    stripe_payment_intent_id = Column(String)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    status = Column(String, default="pending")  # pending, completed, failed, refunded
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    booking = relationship("Booking", back_populates="transactions")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    points = Column(Integer, nullable=False)
    icon = Column(String)
    viral_text = Column(Text)
    reward = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_key = Column(String, nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    shared = Column(Boolean, default=False)
    shared_platform = Column(String)
    shared_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="achievements")

class WearableData(Base):
    __tablename__ = "wearable_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_type = Column(String, nullable=False)  # apple_watch, whoop, fitbit
    data_json = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class UserWearableConnection(Base):
    __tablename__ = "user_wearable_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_type = Column(String, nullable=False)
    auth_token = Column(Text)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User", back_populates="wearable_connections")

class EmailIntegration(Base):
    __tablename__ = "email_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # gmail, outlook
    credentials = Column(Text)
    connected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User", back_populates="email_integrations")

class CalendarIntegration(Base):
    __tablename__ = "calendar_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # google_calendar, outlook
    credentials = Column(Text)
    connected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User", back_populates="calendar_integrations")

class SocialIntegration(Base):
    __tablename__ = "social_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # instagram, facebook, twitter
    access_token = Column(Text)
    provider_user_id = Column(String)
    provider_username = Column(String)
    connected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User", back_populates="social_integrations")

class ZoomIntegration(Base):
    __tablename__ = "zoom_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text)
    zoom_user_id = Column(String)
    email = Column(String)
    connected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User", back_populates="zoom_integrations")

class VirtualSession(Base):
    __tablename__ = "virtual_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trainer_name = Column(String, nullable=False)
    session_type = Column(String)  # training, consultation, group
    start_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    zoom_meeting_id = Column(String)
    zoom_join_url = Column(Text)
    zoom_start_url = Column(Text)
    price = Column(Float)
    status = Column(String, default="scheduled")  # scheduled, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="virtual_sessions")

class SMSLog(Base):
    __tablename__ = "sms_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone_number = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    twilio_sid = Column(String)
    status = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class TwoFactorCode(Base):
    __tablename__ = "two_factor_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone_number = Column(String, nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class SnapchatIntegration(Base):
    __tablename__ = "snapchat_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    snapchat_id = Column(String, nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    username = Column(String)
    display_name = Column(String)
    bitmoji_avatar = Column(String)
    bitmoji_selfie = Column(String)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User")

class TikTokIntegration(Base):
    __tablename__ = "tiktok_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tiktok_id = Column(String, nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    username = Column(String)
    display_name = Column(String)
    follower_count = Column(Integer)
    following_count = Column(Integer)
    avatar_url = Column(String)
    verified = Column(Boolean, default=False)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime)
    status = Column(String, default="connected")  # connected, disconnected, error
    
    # Relationships
    user = relationship("User")

class ViralShare(Base):
    __tablename__ = "viral_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    platform = Column(String, nullable=False)  # snapchat, tiktok, instagram, facebook
    content_type = Column(String, nullable=False)  # achievement, streak, workout, milestone
    share_id = Column(String)  # Platform-specific share ID
    share_url = Column(String)
    engagement_data = Column(JSON)  # Likes, comments, shares, etc.
    shared_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    achievement = relationship("Achievement")

# Marketplace Model
class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # "sell" or "rent"
    rental_period = Column(String)  # "per day", "per week", "per month", etc.
    condition = Column(String, nullable=False)  # "New", "Like New", "Good", "Fair"
    category = Column(String, nullable=False, index=True)  # basketball, tennis, golf, etc.
    
    # Seller information
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_name = Column(String)
    seller_rating = Column(Float, default=5.0)
    
    # Location
    zip_code = Column(String, nullable=False, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Media
    image = Column(String)
    
    # Status
    is_available = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("User", back_populates="marketplace_listings")
