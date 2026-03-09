from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base

class Outflow(Base):
    __tablename__ = "outflows"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    site_id = Column(String, index=True)
    company = Column(String, index=True)
    status = Column(Integer)

    status_start = Column(DateTime, nullable=True)
    latest_event_start = Column(DateTime, nullable=True)
    latest_event_end = Column(DateTime, nullable=True)

    latitude = Column(Float)
    longitude = Column(Float)

    receiving_watercourse = Column(String)
    last_updated = Column(DateTime)