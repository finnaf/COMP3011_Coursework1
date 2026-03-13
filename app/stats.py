from sqlalchemy import func, case, distinct
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Outflow, WaterCompany

def get_company_performance_stats(db: Session, ticker: str = None):
    now = datetime.now()

    duration_calculation = func.sum(
        func.julianday(func.coalesce(Outflow.latest_event_end, now)) - 
        func.julianday(Outflow.latest_event_start)
    )

    query = db.query(
        WaterCompany.name,
        WaterCompany.ticker,
        func.count(Outflow.id).label("total_sites"),
        func.sum(case((Outflow.status == 1, 1), else_=0)).label("active_now"),
        func.sum(case((Outflow.status == -1, 1), else_=0)).label("deactivated"),
        duration_calculation.label("total_duration_days")
    ).join(Outflow, WaterCompany.ticker == Outflow.company_ticker)

    # early filter
    if ticker:
        result = query.filter(WaterCompany.ticker == ticker.upper()).first()
        return result

    return query.group_by(WaterCompany.ticker).all()

def get_outflow_stats(db: Session):
    return db.query(
        func.count(Outflow.id).label("total_sites"),
        func.sum(case((Outflow.status == 1, 1), else_=0)).label("active_now"),
        func.sum(case((Outflow.status == -1, 1), else_=0)).label("offline_now"),
        
        func.count(distinct(Outflow.receiving_watercourse)).label("unique_waterways"),
        
        func.sum(
            func.julianday(func.coalesce(Outflow.latest_event_end, func.now())) - 
            func.julianday(Outflow.latest_event_start)
        ).label("total_spill_days"),
        
        func.max(Outflow.last_updated).label("last_sync")
    ).first()

def get_general_stats(db: Session):
    return db.query(
        func.count(Outflow.id).label("total_records"),
        func.min(Outflow.latest_event_start).label("earliest_event"),
        func.max(Outflow.latest_event_start).label("latest_event"),
        func.min(Outflow.latitude).label("lat_min"),
        func.max(Outflow.latitude).label("lat_max"),
        func.min(Outflow.longitude).label("lon_min"),
        func.max(Outflow.longitude).label("lon_max"),
        func.avg(
            func.julianday(Outflow.latest_event_end) - 
            func.julianday(Outflow.latest_event_start)
        ).label("avg_duration_days")
    ).first()

def get_top_watercourse(db: Session):
    return db.query(
        Outflow.receiving_watercourse,
        func.count(Outflow.id).label("count")
    ).group_by(Outflow.receiving_watercourse).order_by(func.count(Outflow.id).desc()).first()