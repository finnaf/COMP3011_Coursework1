from fastapi import FastAPI, Depends, HTTPException, Response
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import SessionLocal, engine
from app.models import Base, Outflow
from app.utils.import_csv import import_csv
import os

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/outflows/{id}", response_model=schemas.Outflow)
def read_outflow(id: int, db: Session = Depends(get_db)):
    result = crud.get_outflow(db, id)
    if not result:
        raise HTTPException(404, "Not found")
    return result

@app.get("/outflows/", response_model=list[schemas.Outflow])
def read_outflows(
    company: str | None = None,
    watercourse: str | None = None,
    db: Session = Depends(get_db)
):
    return crud.get_outflows(db, company, watercourse)

@app.post("/outflows/", response_model=schemas.Outflow)
def create(data: schemas.OutflowCreate, db: Session = Depends(get_db)):
    return crud.create_outflow(db, data)

@app.put("/outflows/{id}")
def update(id: int, data: dict, db: Session = Depends(get_db)):
    updated = crud.update_outflow(db, id, data)
    if not updated:
        raise HTTPException(404, "Not found")
    return updated

@app.delete("/outflows/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    ok = crud.delete_outflow(db, id)
    if not ok:
        raise HTTPException(404, "Not found")
    return {"deleted": True}

# silence 404 icon request by browser
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")