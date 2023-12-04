import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
DATASOURCE_URL = os.getenv('DATASOURCE_URL', 'mysql+mysqldb://root:12345678@127.0.0.1:3306/uassistant?charset=utf8mb4&')
# DATASOURCE_URL = os.getenv('DATASOURCE_URL', 'postgresql://root:LQSrJuf3nSdEchzulbMrkVOyIsuDg0fx@dpg-ck55avug2bec73cgb9og-a.oregon-postgres.render.com/assistai')
engine = create_engine(url=DATASOURCE_URL, pool_recycle=3600, pool_size=10)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()