#!/usr/bin/env python3.7

import logging
from sqlalchemy import schema 
from scripts.db import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey, PickleType


class Message(Base):
    '''This is the main messages model...
       It is related to the Server model...
       It stores all the messages from connected servers...
    '''

    __tablename__ = 'messages'

    id = Column(Integer, Sequence('message_id_seq'), primary_key=True)
    sender = Column(String(100))
    serial = Column(String(5))
    size = Column(String(10))
    name = Column(String())

    server_id = Column(Integer, ForeignKey('servers.id'))
    server = relationship("Server", back_populates="messages")

    # __table_args__ = (schema.UniqueConstraint('sender', 'name', 'size', 'serial', name='_message_uc'), {})

    def __repr__(self):
        return "<User(sender='%s', serial='%s', size='%s', name='%s')>" % (self.sender, self.serial, self.size, self.name)




class Server(Base):
    '''This stores the servers that have ever been connected to...
       It's id is stored in the messages to relate them...
    '''
    __tablename__ = 'servers'

    id = Column(Integer, Sequence('server_id_seq'), primary_key=True)
    server = Column(String(25))
    channel = Column(String(25))

    # __table_args__ = (schema.UniqueConstraint('server', 'channel', name='_message_uc'), {})
 
    def __repr__(self):
        return "<User(server='%s', channel='%s')>" % (self.server, self.channel)
    
Server.messages = relationship("Message", order_by = Message.id, back_populates="server")


# Server real-server port channel_id 

class AddedServers(Base):
    '''This stores all the servers added and all their info..'''
    
    __tablename__ = 'added_servers'

    id = Column(Integer, Sequence('current_server_id_seq'), primary_key=True)
    server = Column(String(40), nullable=False)
    real_server = Column(String(50))
    port = Column(Integer(), nullable=False)
    channels = Column(PickleType())
    on_instance = Column(String(), nullable=False)
    status = Column(PickleType())