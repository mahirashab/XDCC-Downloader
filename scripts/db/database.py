#!./env/bin/python3

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = db.create_engine('sqlite:///main_db.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


session = Session()

def init_db():
    from scripts.db.models import Message
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)





