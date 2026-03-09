from typing import Optional
from datetime import datetime
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from .models import Outflow, APIKey
from .schemas import OutflowBase
from .security import generate_api_key

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
        query = query.filter(Outflow.company == company)
    if watercourse:
        query = query.filter(Outflow.receiving_watercourse.ilike(watercourse))

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
    obj = get_outflow(db, id)
    if not obj:
        return None
    for k, v in data.items():
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