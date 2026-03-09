from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Outflow
from .schemas import OutflowCreate

def get_outflow(db: Session, id: int):
    return db.execute(select(Outflow).where(Outflow.id == id)).scalar_one_or_none()

def get_outflows(db: Session, 
    company: str | None = None,
    watercourse: str | None = None,
):
    stmt = select(Outflow)
    if company:
        stmt = stmt.where(Outflow.company == company)
    if watercourse:
        stmt = stmt.where(Outflow.receiving_watercourse.ilike(watercourse))
    return db.execute(stmt).scalars().all()

def create_outflow(db: Session, data: OutflowCreate):
    obj = Outflow(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_outflow(db: Session, objectid: int, data: dict):
    obj = get_outflow(db, objectid)
    if not obj:
        return None
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete_outflow(db: Session, objectid: int):
    obj = get_outflow(db, objectid)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True