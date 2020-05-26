
from functools import wraps
from scripts.bot import Main_Bot
from flask import request, jsonify
from flask_restful import Resource
from marshmallow import ValidationError
from scripts.db.models import AddedServers
from scripts.db.schema import ServerSchema, ChannelSchema, AddedServersSchema


def fixed_channels(channels):
    return ['#' + channel 
                if not (channel.startswith('&') or channel.startswith('#'))
                else channel 
                for channel in channels]

def add_channels(server, channels):
    # Adds if any extra channels are found...
    #
    channels = fixed_channels(channels) # Fix the channel names...

    client = Main_Bot.client_hash_table[server] # Get client from hash table...

    # Set the new updated channels list...
    unique = set(client.channels + channels)
    client.channels = list(unique)

    AddedServers.update_info(client.server, {'channels': client.channels}) # Update info in db...


def remove_channels(server, channels):
    # Removes given channels...
    #
    channels = fixed_channels(channels) # Fix the channel names...

    client = Main_Bot.client_hash_table[server] # Get client from hash table...

    # Set the new updated channels list...
    new_channels_list = set(client.channels) - set(channels)
    client.channels = list(new_channels_list)

    # Update info in db...
    AddedServers.update_info(client.server, {
                                            'channels': client.channels
                                        })


def add_and_connect_server(payload):
    # Creates a client fron given data...
    # 
    server, channels = payload['server'], payload['channels'] # Get server name and channels...
    port = payload.get('port', 6667) # Get port. if not found 6667 is used...
    
    channels = fixed_channels(channels) # Fix the channel names...

    # Creates new server and save to db...
    new_server = AddedServers(server, port, channels)
    new_server.save_to_db()

    # Creates new client and sets hash...
    client = Main_Bot.create_client()
    Main_Bot.client_hash_table[server] = client
    print(Main_Bot.client_hash_table)

    # Connect the client to server...
    client.connect(server, channels,
            port=payload.get('port', 6667),
            nick=payload.get('nick', None),
            user=payload.get('user', None), 
            real=payload.get('real', None),
            ssl=payload.get('ssl', None),
            password=payload.get('password', None))



def check_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        payload = request.get_json()
        if not payload:
            resp = {
                'message': 'No json data found in request.'
            }
            return jsonify(resp)

        return f(*args, **kws)
    return decorated_func


def varify_server_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):

        try:
            payload = request.get_json()
            varified_payload = ServerSchema().load(payload)
        except ValidationError as err:
            resp = {
                'message': err.messages
            }
            return jsonify(resp)

        return f(payload=varified_payload, *args, **kws)
    return decorated_func



class Server(Resource):

    def get(self):
        server_schema = AddedServersSchema() # Creates schema to dump data...
        servers = AddedServers.query.all() # Gets all the servers...

        payload = [ # Create payload from all the servers data...
            server_schema.dump(server) for server in servers
        ]

        return jsonify({
            'Data': payload
        })

    @check_payload
    @varify_server_payload
    def post(self, payload=None):
        server, channels = payload['server'], payload['channels'] # Get server name and channels...

        server_exists = AddedServers.has_server(server) # Check if server exists...

        if server_exists: # Server exists. New channels are added...
            add_channels(server, channels)
            return jsonify({
                "message": "Server already exists. The new channels are added."
            })
        else: # Server dosen't exist. Server connected and saved to db...
            add_and_connect_server(payload)
            return jsonify({
                "message": "Added and connected to server."
            })

    @check_payload
    @varify_server_payload
    def delete(self, payload=None):
        server, channels = payload['server'], payload['channels'] # Get server name and channels...

        match = AddedServers.get_server_name(server) # Get server from db...

        if not match: # No server found...
            return jsonify({
                "message": "No such server connected."
            })

        # Getting client connected to server...
        client = Main_Bot.client_hash_table[server]

        Main_Bot.remove_client(client) # Remove the client..
        match.delete_from_db() # Delete server from db...

        return jsonify({
            "message": "Server disconnected and removed"
        })


def varify_channel_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        try:
            payload = request.get_json()
            varified_payload = ChannelSchema().load(payload)
        except ValidationError as err:
            resp = {'message': err.messages}
            return jsonify(resp)

        return f(payload=varified_payload, *args, **kws)
    return decorated_func


class Channel(Resource):

    @check_payload
    @varify_channel_payload
    def post(self, payload=None):
        server, channels = payload['server'], payload['channels'] # Get server name and channels...

        server_exists = AddedServers.has_server(server) # Check if server exists...

        if server_exists: # Server exists. New channels are added...
            add_channels(server, channels)
            return jsonify({
                "message": "The new channels were added."
            })
        else: # Server dosen't exist. Server connected and saved to db...
            add_and_connect_server(payload)
            return jsonify({
                "message": 'Server was not Found. Connected to server and joined channel.'
            })

    @check_payload
    @varify_channel_payload
    def delete(self, payload=None):
        server, channels = payload['server'], payload['channels'] # Get server name and channels...

        server_exists = AddedServers.has_server(server) # Check if server exists...

        if server_exists: # Server exists. New channels are removed...
            remove_channels(server, channels)
            return jsonify({
                "message": "The channels were removed."
            })
        else: # Server dosen't exist.
            return jsonify({
                "message": "No such server.."
            })
