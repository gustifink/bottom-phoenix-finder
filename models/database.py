from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool

Base = declarative_base()

class Token(Base):
    __tablename__ = "tokens"
    
    address = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    chain = Column(String, index=True)
    current_price = Column(Float)
    ath_price = Column(Float)
    ath_date = Column(DateTime)
    crash_percentage = Column(Float)
    liquidity_usd = Column(Float)
    volume_24h = Column(Float)
    market_cap = Column(Float)
    first_seen_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    brs_scores = relationship("BRSScore", back_populates="token")
    alerts = relationship("Alert", back_populates="token")
    watchlist_entries = relationship("Watchlist", back_populates="token")

class BRSScore(Base):
    __tablename__ = "brs_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_address = Column(String, ForeignKey("tokens.address"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    brs_score = Column(Float, nullable=False)
    holder_resilience_score = Column(Float)
    volume_floor_score = Column(Float)
    price_recovery_score = Column(Float)
    distribution_health_score = Column(Float)
    revival_momentum_score = Column(Float)
    smart_accumulation_score = Column(Float)
    
    # Additional metrics
    buy_sell_ratio = Column(Float)
    volume_trend = Column(String)  # up, down, stable
    price_trend = Column(String)    # up, down, stable
    
    # Relationship
    token = relationship("Token", back_populates="brs_scores")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_address = Column(String, ForeignKey("tokens.address"), nullable=False)
    alert_type = Column(String, nullable=False)  # phoenix_rising, showing_life, etc
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(String)
    sent_status = Column(Boolean, default=False)
    score_at_alert = Column(Float)
    
    # Relationship
    token = relationship("Token", back_populates="alerts")

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_address = Column(String, ForeignKey("tokens.address"), nullable=False)
    user_id = Column(String)  # Could be telegram user id
    added_date = Column(DateTime, default=datetime.utcnow)
    alert_threshold = Column(Float, default=80.0)
    active = Column(Boolean, default=True)
    
    # Relationship
    token = relationship("Token", back_populates="watchlist_entries")

# Database connection setup
def get_engine(database_url: str = "sqlite:///./bottom.db"):
    if "sqlite" in database_url:
        # SQLite specific settings for better concurrency
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        engine = create_engine(database_url, echo=False)
    return engine

def init_db(database_url: str = "sqlite:///./bottom.db"):
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine

def get_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal() 