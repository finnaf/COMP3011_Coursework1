import os, math, sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./outflows.db")

# currently using sqlite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

@event.listens_for(Engine, "connect")
def register_math_functions(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("sqrt", 1, math.sqrt)
        dbapi_connection.create_function("sin", 1, math.sin)
        dbapi_connection.create_function("cos", 1, math.cos)
        dbapi_connection.create_function("asin", 1, math.asin)
        dbapi_connection.create_function("radians", 1, math.radians)
        dbapi_connection.create_function("pow", 2, math.pow)

def get_engine():
    return engine