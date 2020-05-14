#!/usr/bin/env python3.7

from marshmallow import Schema, fields
from scripts.db.models import AddedServers
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field



class ServerSchema(Schema):
    server = fields.Str()
    port = fields.Integer()
    channels = fields.List(fields.Str())

class ChannelSchema(Schema):
    server = fields.Str()
    channels = fields.List(fields.Str())


class AddedServersSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AddedServers
        include_relationships = True
        load_instance = True

