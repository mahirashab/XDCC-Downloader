#!./env/bin/python3

import os
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

'''Getting the env variables set by docker-compose...'''
user = os.environ.get('USER')
password = os.environ.get('PASSWORD')
db_name = os.environ.get('DB')

'''Creating custom connection string...'''
connect_string = f'postgresql+psycopg2://{user}:{password}@postgres-db:5432/{db_name}'

'''Setting up the connection...'''
engine = db.create_engine(connect_string, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

session = Session()

'''Sets up all the models...'''
def init_db():
    from scripts.db.models import Message, Server
    Base.metadata.create_all(engine)





