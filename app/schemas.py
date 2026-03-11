from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class OutflowBase(BaseModel):
    site_id: Optional[str] = None
    company_ticker: Optional[str] = None
    status: Optional[int] = None
    status_start: Optional[datetime] = None
    latest_event_start: Optional[datetime] = None
    latest_event_end: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    receiving_watercourse: Optional[str] = None
    last_updated: Optional[datetime] = None

class Outflow(OutflowBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WaterCompanyBase(BaseModel):
    ticker: str
    name: str
    region: Optional[str] = None
    website: Optional[str] = None

# so puts can change any field
class WaterCompanyUpdate(BaseModel):
    ticker: Optional[str] = None
    name: Optional[str] = None
    region: Optional[str] = None
    website: Optional[str] = None

class WaterCompany(WaterCompanyBase):
    model_config = ConfigDict(from_attributes=True)


class APIKeyCreate(BaseModel):
    active: bool = True
    owner: Optional[str] = None
    
class APIKey(APIKeyCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# stat return schemas
class CompanyStats(BaseModel):
    name: str
    ticker: str
    total_sites: int
    active_now: int
    deactivated: int
    total_duration_days: float | None # julianday

    class Config:
        from_attributes = True