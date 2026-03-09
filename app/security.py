import hashlib, secrets, os
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import APIKey

# avoid circular import
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

load_dotenv()

# admin key set to foo for coursework, not production code
ADMIN_KEY = os.getenv("ADMIN_KEY", "foo")

api_key_header = APIKeyHeader(name="X-API_KEY")

async def verify_api_key(key: str = Security(api_key_header), db: Session = Depends(get_db)):
    '''
    Checks the given API key matches a stored key.
    '''
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    
    stored = db.query(APIKey).filter(APIKey.key == hashed_key, APIKey.active == True).first()
    if not stored:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return stored

def generate_api_key():
    user_key = secrets.token_urlsafe(32)
    hashed_key = hashlib.sha256(user_key.encode()).hexdigest()
    
    return user_key, hashed_key

async def verify_admin(key: str = Security(api_key_header)):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")