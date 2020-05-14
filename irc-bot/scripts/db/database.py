#!/usr/bin/env python3.7

import os
import logging
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

activity_logger = logging.getLogger("ActivityLogger")

# Getting the env variables set by docker-compose...
activity_logger.info('Getting the env variables for db connection.')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

# Creating custom connection string...
activity_logger.info('Connecting to db with user %s password %s db_name %s', user, password, db_name)
connect_string = f'postgresql+psycopg2://{user}:{password}@postgres-db:5432/{db_name}'


# Setting up the connection...
activity_logger.info('Setting up the sqlalchemy db engine and Session.')
engine = db.create_engine(connect_string, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

session = Session()

'''Sets up all the models...'''
def init_db():
    from scripts.db.models import Message, Server, AddedServers
    # Base.metadata.drop_all(engine)
    activity_logger.info('Initiating db..')
    Base.metadata.create_all(engine)

    # delete all previous servers
    activity_logger.info('Dropping the AddedServers table content.')
    session.query(AddedServers).delete()
    session.commit()





