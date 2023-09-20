import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# mysql+mysqldb://root:12345678@192.168.9.38:3306/assistai?charset=utf8mb4&
DATASOURCE_URL = os.getenv('DATASOURCE_URL', 'postgresql://root:LQSrJuf3nSdEchzulbMrkVOyIsuDg0fx@dpg-ck55avug2bec73cgb9og-a.oregon-postgres.render.com/assistai')
engine = create_engine(url=DATASOURCE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()