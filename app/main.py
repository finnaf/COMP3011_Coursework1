from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.exceptions import ResponseValidationError, RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import SessionLocal, engine
from app.models import Base, Outflow
from app.utils.import_csv import import_csv
from app.security import get_db
from app.stats import get_company_performance_stats, get_outflow_stats
import os

# on startup
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()    
    count = db.query(Outflow).count()
    if count == 0:
        print("Database empty. Fetching data from streamwaterdata...")
        
        crud.seed_companies(db)

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
@app.get("/outflows/", 
    response_model=list[schemas.Outflow],
    status_code=200)
def read_outflows(
    company: Optional[str] = None,
    watercourse: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    return crud.get_outflows(db, company, watercourse, lat, lon, radius_km, limit, skip)

@app.get("/outflows/{id}",
    response_model=schemas.Outflow,
    status_code=200)
def read_outflow(id: int, db: Session = Depends(get_db)):
    result = crud.get_outflow(db, id)
    if not result:
        raise HTTPException(404, "Not found")
    return result

@app.post("/outflows/", 
    response_model=schemas.Outflow,
    dependencies=[Depends(security.verify_api_key)],
    status_code=201)
def create_outflow(data: schemas.OutflowBase, db: Session = Depends(get_db)):
    return crud.create_outflow(db, data)

@app.put("/outflows/{id}",
    response_model=schemas.Outflow,
    dependencies=[Depends(security.verify_api_key)],
    status_code=200)
def update_outflow(id: int, data: schemas.OutflowBase, db: Session = Depends(get_db)):
    updated = crud.update_outflow(db, id, data)
    if not updated:
        raise HTTPException(404, "Not found")
    return updated

@app.delete("/outflows/{id}", dependencies=[Depends(security.verify_api_key)])
def delete_outflow(id: int, db: Session = Depends(get_db)):
    ok = crud.delete_outflow(db, id)
    if not ok:
        raise HTTPException(404, "Not found")
    return Response(status_code=204)


# water companies
@app.get("/companies/", 
    response_model=list[schemas.WaterCompany],
    status_code=200)
def read_companies(
    name: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    return crud.get_companies(db, name=name, region=region, limit=limit, skip=skip)

@app.get("/companies/{ticker}", 
    response_model=schemas.WaterCompany,
    status_code=200)
def read_company(ticker: str, db: Session = Depends(get_db)):
    result = crud.get_company(db, ticker)
    if not result:
        raise HTTPException(404, "Not found")
    return result

@app.post("/companies/",
    response_model=schemas.WaterCompany,
    dependencies=[Depends(security.verify_api_key)],
    status_code=201)
def create_company(data: schemas.WaterCompanyBase, db: Session = Depends(get_db)):
    existing = crud.get_company(db, data.ticker)
    if existing:
        raise HTTPException(400, f"Company with ticker '{data.ticker}' already exists")
    return crud.create_company(db, data)

@app.put("/companies/{ticker}", 
    response_model=schemas.WaterCompany,
    dependencies=[Depends(security.verify_api_key)],
    status_code=200)
def update_company(ticker: str, data: schemas.WaterCompanyUpdate, db: Session = Depends(get_db)):
    updated = crud.update_company(db, ticker, data)
    if not updated:
        raise HTTPException(404, "Not found")
    return updated

@app.delete("/companies/{ticker}", dependencies=[Depends(security.verify_api_key)])
def delete_company(ticker: str, db: Session = Depends(get_db)):
    ok = crud.delete_company(db, ticker)
    if not ok:
        raise HTTPException(404, "Not found")
    return Response(status_code=204)

# authentication
@app.post("/auth/keys", dependencies=[Depends(security.verify_admin)])
def create_key(data: schemas.APIKeyCreate, db: Session = Depends(get_db)):
    user_key, db_key = crud.create_api_key(db, owner=data.owner, active=data.active)
    return JSONResponse(
        {"id": db_key.id, "key": user_key, "owner": db_key.owner, "active": db_key.active},
        status_code=201
    )

@app.put("/auth/keys/{id}", dependencies=[Depends(security.verify_admin)])
def rotate_key(id: int, db: Session = Depends(get_db)):
    '''
    For compromised API keys. Deactivates the old key and generates a completely new key.
    '''
    user_key, db_key = crud.rotate_api_key(db, id)
    if not (user_key or db_key):
        raise HTTPException(404, "API key not found")
    return JSONResponse(
        {"id": db_key.id, "key": user_key, "owner": db_key.owner, "active": db_key.active},
        status_code=201
    )

@app.delete("/auth/keys/{id}", dependencies=[Depends(security.verify_admin)])
def delete_key(id: int, db: Session = Depends(get_db)):
    ok = crud.delete_api_key(db, id)
    if not ok:
        raise HTTPException(404, "Not found")
    return Response(status_code=204)


# stats
@app.get("/")
@app.get("/stats")
def foo():
    return Response(status_code=200)

@app.get("/stats/outflows/", status_code=200)
def read_outflow_stats(db: Session = Depends(get_db)):
    stats = get_outflow_stats(db)
    
    active_pct = (stats.active_now / stats.total_sites * 100) if stats.total_sites > 0 else 0
    
    return {
        "summary": {
            "total_sites": stats.total_sites,
            "active_now": stats.active_now,
            "offline_now": stats.offline_now,
            "active_percentage": round(active_pct, 2)
        },
        "environmental_impact": {
            "unique_waterways_affected": stats.unique_waterways,
            "total_discharge_hours": round((stats.total_spill_days or 0) * 24, 1)
        },
        "metadata": {
            "last_updated": stats.last_sync
        }
    }

@app.get("/stats/companies", 
    response_model=list[schemas.CompanyStats],
    status_code=200)
def get_companies_stats(db: Session = Depends(get_db)):
    return get_company_performance_stats(db)


# exception handlers
@app.exception_handler(RequestValidationError)
async def request_validation_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(ResponseValidationError)
async def response_validation_handler(request, exc):
    print("RESPONSE VALIDATION ERROR:", exc.errors())
    return JSONResponse(status_code=500, content={"detail": str(exc.errors())})

# icon request by browser
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")