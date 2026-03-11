from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from .database import Base


class WaterCompany(Base):
    __tablename__ = "companies"

    ticker = Column(String(6), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    region = Column(String, nullable=True)
    website = Column(String, nullable=True)


class Outflow(Base):
    __tablename__ = "outflows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String(12)) # e.g. "SVT-02591"
    company_ticker = Column(String(6), ForeignKey("companies.ticker"), nullable=True, index=True)
    status = Column(Integer)
    status_start = Column(DateTime, nullable=True)
    latest_event_start = Column(DateTime, nullable=True)
    latest_event_end = Column(DateTime, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    receiving_watercourse = Column(String)
    last_updated = Column(DateTime)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String, index=True, unique=True, nullable=False)
    owner = Column(String)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)