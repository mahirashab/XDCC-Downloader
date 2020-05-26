
from scripts.db import db

class AddedServers(db.Model):
    '''This stores all the servers added and all their info..'''
    
    __tablename__ = 'added_servers'

    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String(40), nullable=False)
    port = db.Column(db.Integer(), nullable=False)
    channels = db.Column(db.PickleType())

    real_server = db.Column(db.String(50))
    status = db.Column(db.PickleType()) 


    def __init__(self, server, port, channels):
        self.server = server
        self.port = port
        self.channels = channels

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def update_info(cls, server_name, info_dict):
        cls.query.filter_by(server=server_name).update(info_dict)
        db.session.commit()
    
    @classmethod
    def has_server(cls, server_name):
        server = cls.query.filter_by(server=server_name).first()
        return True if server else False

    @classmethod
    def get_server_name(cls, server_name):
        return cls.query.filter_by(server=server_name).first() 

    @classmethod
    def delete_server(cls, server_name):
        server = cls.query.filter_by(server=server_name).first()
        db.session.delete(server)
        db.session.commit()

