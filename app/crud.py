from typing import Optional
from datetime import datetime
from dateutil import parser as dateparser
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Outflow, WaterCompany, APIKey
from .schemas import OutflowBase, WaterCompanyBase, WaterCompanyUpdate
from .security import generate_api_key


WATER_COMPANIES = [
    {"ticker": "AWS", "name": "Anglian Water Services", "region": "East of England",        "website": "https://www.anglianwater.co.uk"},
    {"ticker": "NWL", "name": "Northumbrian Water Ltd", "region": "North East England",     "website": "https://www.nwl.co.uk"},
    {"ticker": "SVT", "name": "Severn Trent Water",     "region": "Midlands",               "website": "https://www.severntrent.com"},
    {"ticker": "SBB", "name": "South West Water",   "region": "South West England",     "website": "https://www.southwestwater.co.uk"},
    {"ticker": "SWS", "name": "Southern Water",     "region": "South East England",     "website": "https://www.southernwater.co.uk"},
    {"ticker": "TWL", "name": "Thames Water",       "region": "London & Thames Valley", "website": "https://www.thameswater.co.uk"},
    {"ticker": "UUP", "name": "United Utilities",   "region": "North West England",     "website": "https://www.unitedutilities.com"},
    {"ticker": "WXW", "name": "Wessex Water",       "region": "South West England",     "website": "https://www.wessexwater.co.uk"},
    {"ticker": "YWS", "name": "Yorkshire Water",    "region": "Yorkshire",              "website": "https://www.yorkshirewater.com"},
]

def seed_companies(db: Session):
    if db.query(WaterCompany).count() == 0:
        for data in WATER_COMPANIES:
            db.add(WaterCompany(**data))
        db.commit()

def get_company(db: Session, ticker: str):
    return db.execute(select(WaterCompany).where(WaterCompany.ticker == ticker.upper())).scalar_one_or_none()

def get_companies(
    db: Session,
    name: str | None = None,
    region: str | None = None,
    limit: int = 100,
    skip: int = 0,
):
    q = db.query(WaterCompany)
    if name:
        q = q.filter(WaterCompany.name.ilike(f"%{name}%"))
    if region:
        q = q.filter(WaterCompany.region.ilike(f"%{region}%"))
    return q.offset(skip).limit(limit).all()

def create_company(db: Session, data: WaterCompanyBase):
    company = WaterCompany(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

def update_company(db: Session, ticker: str, data: WaterCompanyUpdate):
    company = db.query(WaterCompany).filter(WaterCompany.ticker == ticker.upper()).first()
    if not company:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company

def delete_company(db: Session, ticker: str):
    company = db.query(WaterCompany).filter(WaterCompany.ticker == ticker.upper()).first()
    if not company:
        return False
    db.delete(company)
    db.commit()
    return True


# outflow
def get_outflow(db: Session, id: int):
    return db.execute(select(Outflow).where(Outflow.id == id)).scalar_one_or_none()

def get_outflows(
    db: Session,
    company: Optional[str] = None,
    watercourse: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    limit: int = 100,
    skip: int = 0,
):
    query = db.query(Outflow)

    if company:
        match = next((c["ticker"] for c in WATER_COMPANIES if c["name"].lower() == company.lower()), None)
        ticker = match or company.upper()  # can also just pass ticker
        query = query.filter(Outflow.company_ticker == ticker)
    if watercourse:
        query = query.filter(Outflow.receiving_watercourse.ilike(f"%{watercourse}%"))

    if lat is not None and lon is not None:
        # haversine distance
        lat_r = func.radians(lat)
        lon_r = func.radians(lon)
        olat_r = func.radians(Outflow.latitude)
        olon_r = func.radians(Outflow.longitude)

        distance_km = (
            6371 * 2 * func.asin(func.sqrt(
                func.pow(func.sin((olat_r - lat_r) / 2), 2) +
                func.cos(lat_r) * func.cos(olat_r) *
                func.pow(func.sin((olon_r - lon_r) / 2), 2)
            ))
        )

        if radius_km:
            query = query.filter(distance_km <= radius_km)

        query = query.order_by(distance_km)

    return query.offset(skip).limit(limit).all()

def create_outflow(db: Session, data: OutflowBase):
    obj = Outflow(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_outflow(db: Session, id: int, data: dict):
    DATETIME_FIELDS = {"status_start", "latest_event_start", "latest_event_end", "last_updated"}

    obj = get_outflow(db, id)
    if not obj:
        return None
    for k, v in data.items():
        if k in DATETIME_FIELDS and isinstance(v, str):
            v = dateparser.parse(v)
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete_outflow(db: Session, id: int):
    obj = get_outflow(db, id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# authentication (no read)
def create_api_key(db: Session, owner: Optional[str], active: bool = True):
    user_key, hashed_key = generate_api_key()
    
    db_key = APIKey(
        key=hashed_key,
        active=active,
        owner=owner
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return user_key, db_key

def get_api_key(db: Session, id: int):
    return db.execute(select(APIKey).where(APIKey.id == id)).scalar_one_or_none()

def rotate_api_key(db: Session, id: int):
    old = db.execute(select(APIKey).where(APIKey.id == id)).scalar_one_or_none()
    if not old:
        return None

    user_key, hashed_key = generate_api_key()
    new_key = APIKey(
        key=hashed_key,
        active=True,
        owner=old.owner,
        created_at=datetime.now()
    )
    
    db.add(new_key)
    old.active = False
    
    db.commit()
    db.refresh(new_key)
    return user_key, new_key

def delete_api_key(db: Session, id: int):
    key = db.execute(select(APIKey).where(APIKey.id == id)).scalar_one_or_none()
    if not key:
        return False
    db.delete(key)
    db.commit()
    return True