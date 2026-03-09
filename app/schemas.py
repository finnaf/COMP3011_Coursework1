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

class OutflowCreate(OutflowBase):
    pass

class Outflow(OutflowBase):
    id: int

    class Config:
        from_attributes = True