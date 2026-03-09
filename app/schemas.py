from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OutflowBase(BaseModel):
    site_id: Optional[str]
    company: Optional[str]
    status: Optional[int]
    status_start: Optional[datetime]
    latest_event_start: Optional[datetime]
    latest_event_end: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    receiving_watercourse: Optional[str]
    last_updated: Optional[datetime]

class Outflow(OutflowBase):
    id: int

    class Config:
        from_attributes = True


class WaterCompanyBase(BaseModel):
    ticker: str
    name: str
    region: Optional[str] = None
    website: Optional[str] = None

class WaterCompany(WaterCompanyBase):
    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    active: bool
    owner: Optional[str]
    
class APIKey(APIKeyCreate):
    id: int
    
    class Config:
        from_attributes = True