from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Get URL from docker-compose environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the connection engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- THE MODEL (Your Table Structure) ---
class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)        # e.g., "Financial Modeling Prep"
    headline = Column(String)
    sentiment = Column(String)     # Positive/Negative
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Function to create tables automatically
def init_db():
    Base.metadata.create_all(bind=engine)