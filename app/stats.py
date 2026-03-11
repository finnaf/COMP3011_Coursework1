from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Outflow, WaterCompany

def get_company_performance_stats(db: Session):
    duration_calculation = func.sum(
        func.julianday(func.coalesce(Outflow.latest_event_end, func.now())) - 
        func.julianday(Outflow.latest_event_start)
    )

    stats = (
        db.query(
            WaterCompany.name,
            WaterCompany.ticker,
            func.count(Outflow.id).label("total_sites"),
            func.sum(case((Outflow.status == 1, 1), else_=0)).label("active_now"),
            func.sum(case((Outflow.status == -1, 1), else_=0)).label("deactivated"),
            duration_calculation.label("total_duration_days")
        )
        .join(Outflow, WaterCompany.ticker == Outflow.company_ticker)
        .group_by(WaterCompany.ticker)
        .all()
    )
    return stats