

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker



'''Setting up the connection...'''
engine = db.create_engine("sqlite:///irc_bot.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

session = Session()

'''Sets up all the models...'''
def init_db():
    from scripts.db.models import Download
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
