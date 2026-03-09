# run with python -m app.utils.import_csv
# from https://www.streamwaterdata.co.uk/pages/storm-overflows-data
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Outflow
from app.database import engine, Base, SessionLocal
from dateutil import parser

Base.metadata.create_all(bind=engine)

COMPANY_TICKERS = {
    "Anglian Water":       "AWS",
    "Northumbrian Water":  "NWL",
    "Severn Trent Water":  "SVT",
    "South West Water":    "SBB",
    "Southern Water":      "SWS",
    "Thames Water":        "TWL",
    "United Utilities":    "UUP",
    "Wessex Water":        "WXW",
    "Yorkshire Water":     "YWS",
}

def import_csv(path: str):
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={
        "id":                   "site_number",
        "company":              "company_name",
        "status":               "status",
        "statusstart":          "status_start",
        "latesteventstart":     "latest_event_start",
        "latesteventend":       "latest_event_end",
        "latitude":             "latitude",
        "longitude":            "longitude",
        "receivingwatercourse": "receiving_watercourse",
        "lastupdated":          "last_updated",
    })

    db: Session = SessionLocal()

    # dropping x and y as dont need mapping
    # dropping objectId as isnt a unique primary key
    for _, row in df.iterrows():
        company_name = row.get("company_name")
        ticker = COMPANY_TICKERS.get(company_name)
        if not ticker:
            print(f"Warning: unknown company '{company_name}', skipping row")
            continue

        site_number = str(row.get("site_number", "")).strip()
        outflow_id = f"{ticker}-{site_number}"

        record = Outflow(
            id=outflow_id,
            company_ticker=ticker,
            status=row.get("status"),
            status_start=parser.parse(row["status_start"]) if pd.notna(row.get("status_start")) else None,
            latest_event_start=parser.parse(row["latest_event_start"]) if pd.notna(row.get("latest_event_start")) else None,
            latest_event_end=parser.parse(row["latest_event_end"]) if pd.notna(row.get("latest_event_end")) else None,
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            receiving_watercourse=row.get("receiving_watercourse"),
            last_updated=parser.parse(row["last_updated"]) if pd.notna(row.get("last_updated")) else None,
        )
        
        db.merge(record)

    db.commit()
    db.close()


if __name__ == "__main__":
    import_csv("./streamwaterdata/Anglian_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Northumbrian_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Severn_Trent_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/South_West_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Southern_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Thames_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/United_Utilities_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Wessex_Water_Storm_Overflow.csv")
    import_csv("./streamwaterdata/Yorkshire_Water_Storm_Overflow.csv")
    
    print("Successfully imported CSV data")