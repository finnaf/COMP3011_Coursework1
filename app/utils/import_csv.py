# run with python -m app.utils.import_csv
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Outflow
from app.database import engine, Base, SessionLocal
from dateutil import parser

Base.metadata.create_all(bind=engine)

def import_csv(path):
    df = pd.read_csv(path)

    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={
        "id": "id",
        "company": "company_name",
        "status": "status",
        "statusstart": "status_start",
        "latesteventstart": "latest_event_start",
        "latesteventend": "latest_event_end",
        "latitude": "latitude",
        "longitude": "longitude",
        "receivingwatercourse": "receiving_watercourse",
        "lastupdated": "last_updated",
    })

    db: Session = SessionLocal()

    # dropping x and y as dont need mapping
    # dropping objectId as isnt a unique primary key
    for _, row in df.iterrows():
        record = Outflow(
            site_id=row.get("id"),
            company=row.get("company_name"), # should be the same for all rows
            status=row.get("status"),
            status_start=parser.parse(row["status_start"]) if pd.notna(row["status_start"]) else None,
            latest_event_start=parser.parse(row["latest_event_start"]) if pd.notna(row["latest_event_start"]) else None,
            latest_event_end=parser.parse(row["latest_event_end"]) if pd.notna(row["latest_event_end"]) else None,
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            receiving_watercourse=row.get("receiving_watercourse"),
            last_updated=parser.parse(row["last_updated"]) if pd.notna(row["last_updated"]) else None,
        )
        db.add(record)

    db.commit()
    db.close()

    print("db: added" + path)

if __name__ == "__main__":

    
    import_csv("./streamwaterdata/Northumbrian_Water_Storm_Overflow_Activity_2_view_7786664318972578633.csv")
    import_csv("./streamwaterdata/Severn_Trent_Water_Storm_Overflow_Activity_6481331589752484693.csv")
    import_csv("./streamwaterdata/anglian_water.csv")

    print("successfully imported csv data")