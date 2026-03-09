from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Response, Security
from fastapi.security.api_key import APIKeyHeader
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import SessionLocal, engine
from app.models import Base, Outflow, APIKey
from app.utils.import_csv import import_csv
from app.security import get_db
import os

# on startup
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    count = db.query(Outflow).count()
    if count == 0:
        print("Database empty. Fetching data from streamwaterdata...")

        csv_files = [
            "./streamwaterdata/Anglian_Water_Storm_Overflow.csv",
            "./streamwaterdata/Northumbrian_Water_Storm_Overflow.csv",
            "./streamwaterdata/Severn_Trent_Water_Storm_Overflow.csv",
            "./streamwaterdata/South_West_Water_Storm_Overflow.csv",
            "./streamwaterdata/Southern_Water_Storm_Overflow.csv",
            "./streamwaterdata/Thames_Water_Storm_Overflow.csv",
            "./streamwaterdata/United_Utilities_Storm_Overflow.csv",
            "./streamwaterdata/Wessex_Water_Storm_Overflow.csv",
            "./streamwaterdata/Yorkshire_Water_Storm_Overflow.csv"
        ]
        
        for f in csv_files:
            if os.path.exists(f):
                import_csv(f)

    db.close()
    yield

app = FastAPI(lifespan=lifespan, title="UK Storm Overflow API")    


# outflows
@app.get("/outflows/{id}", response_model=schemas.Outflow)
def read_outflow(id: int, db: Session = Depends(get_db)):
    result = crud.get_outflow(db, id)
    if not result:
        raise HTTPException(404, "Not found")
    return result

@app.get("/outflows/", response_model=list[schemas.Outflow])
def read_outflows(
    company: Optional[str] = None,
    watercourse: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_outflows(db, company, watercourse)

@app.post("/outflows/", response_model=schemas.Outflow, dependencies=[Depends(security.verify_api_key)])
def create_outflow(data: schemas.OutflowBase, db: Session = Depends(get_db)):
    return crud.create_outflow(db, data)

@app.put("/outflows/{id}", dependencies=[Depends(security.verify_api_key)])
def update_outflow(id: int, data: dict, db: Session = Depends(get_db)):
    updated = crud.update_outflow(db, id, data)
    if not updated:
        raise HTTPException(404, "Not found")
    return updated

@app.delete("/outflows/{id}", dependencies=[Depends(security.verify_api_key)])
def delete_outflow(id: int, db: Session = Depends(get_db)):
    ok = crud.delete_outflow(db, id)
    if not ok:
        raise HTTPException(404, "Not found")
    return {"deleted": True}


# authentication
@app.post("/auth/keys", dependencies=[Depends(security.verify_admin)])
def create_key(data: schemas.APIKeyCreate, db: Session = Depends(get_db)):
    user_key, db_key = crud.create_api_key(db, owner=data.owner, active=data.active)
    return {"id": db_key.id, "key": user_key, "owner": db_key.owner, "active": db_key.active}


# silence 404 icon request by browser
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")