
from marshmallow import Schema, fields
from scripts.db.models import AddedServers
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field


# Checks the incoming payload for the /server route...
class ServerSchema(Schema):
    server = fields.Str(required=True)
    channels = fields.List(fields.Str(), required=True)
    # Not required. Defaults are used if not found. 
    port = fields.Integer()
    nick = fields.Str()
    user = fields.Str()
    real = fields.Str()

    ssl = fields.Str()
    password = fields.Str()

# Checks the incoming payload for the /channel route...
class ChannelSchema(Schema):
    server = fields.Str(required=True)
    channels = fields.List(fields.Str(), required=True)

# json dumps the addedservers data...
class AddedServersSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AddedServers
        include_relationships = True
        load_instance = True

