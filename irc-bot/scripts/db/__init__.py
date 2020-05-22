#!./.env/bin/python3

import os
import logging
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

connect_string = f'postgresql+psycopg2://{user}:{password}@postgres-db:5432/{db_name}'

# Setting up the connection...
engine = db.create_engine(connect_string)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Creates metadata...
import scripts.db.models as models
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


class DB_Session:
    '''Creates a db session 
       that wortks with the with statement
    '''
    def __enter__(self):
        self.session = Session()
        self.session.expire_on_commit = True
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.commit()
        self.session.close()
        self.session = None

# Drops the AddedServers data...
with DB_Session() as session:
    session.query(models.AddedServers).delete()
