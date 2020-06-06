
from scripts.db import Base, Session
from sqlalchemy import Column, Integer, String, PickleType

class Download(Base):
    '''This stores all the servers added and all their info..'''
    
    __tablename__ = 'downloads'

    id = Column(Integer, primary_key=True)
    server = Column(String(40), nullable=False)
    channel = Column(String(20), nullable=False)
    target = Column(String(20), nullable=False)
    serial = Column(String(5), nullable=False)

    filename = Column(String(200))
    filepath = Column(String(200))

    size = Column(Integer())
    size_on_disk = Column(Integer()) 


    def __init__(self, server, channel, target, serial):
        self.server = server
        self.channel = channel
        self.target = target
        self.serial = serial

    def save_to_db(self):
        session = Session()
        session.add(self)
        session.commit()

    def delete_from_db(self):
        session = Session()
        session.delete(self)
        session.commit()

    @classmethod
    def update_info(cls, server_name, info_dict):
        session = Session()
        session.query(cls).filter(cls.server==server_name).update(info_dict)
        session.commit()
    
    @classmethod
    def has_server(cls, server_name):
        session = Session()
        server = session.query(cls).filter(cls.server==server_name).first()
        return True if server else False

    @classmethod
    def get_server_name(cls, server_name):
        session = Session()
        return session.query.filter_by(server=server_name).first() 

    @classmethod
    def delete_server(cls, server_name):
        session = Session()
        server = session.query(cls).filter(cls.server==server_name).first()
        session.delete(server)
        session.commit()

    @classmethod
    def get_all(cls):
        session = Session()
        return session.query(cls).all()

    @classmethod
    def get_first(cls):
        session = Session()
        task = session.query(cls).filter(cls.id==1).first()
        return task
