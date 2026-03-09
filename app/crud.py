from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Outflow, APIKey
from .schemas import OutflowBase
from .security import verify_admin, generate_api_key

# outflow
def get_outflow(db: Session, id: int):
    return db.execute(select(Outflow).where(Outflow.id == id)).scalar_one_or_none()

def get_outflows(db: Session, 
    company: Optional[str] = None,
    watercourse: Optional[str] = None,
):
    stmt = select(Outflow)
    if company:
        stmt = stmt.where(Outflow.company == company)
    if watercourse:
        stmt = stmt.where(Outflow.receiving_watercourse.ilike(watercourse))
    return db.execute(stmt).scalars().all()

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


# authentication
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