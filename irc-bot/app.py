#!./.env/bin/python3

import os
import json
import socket
import requests
import threading

from functools import wraps
from scripts.bot import irc
from scripts.db import DB_Session
from marshmallow import ValidationError
from scripts.logger import setup_logger
from flask_restful import Resource, Api
from flask import Flask, request, jsonify
from scripts.db.models import AddedServers
from scripts.db.schema import ServerSchema, ChannelSchema, AddedServersSchema

setup_logger()

Main_Bot = irc.IRC_Bot_Object()
IRC_Bot_thread = threading.Thread(target=Main_Bot.process_forever, daemon=True)

PORT = 5000

app = Flask(__name__)
api = Api(app)


def redirect_req(url, method, payload):
    # Sends request to the connection host instance...
    #
    url = 'http://' + url
    method = method.lower()

    if method == 'post':
        response = requests.post(url, data=payload)
    elif method == 'delete':
        response = requests.delete(url, data=payload)

    return response.json(), response.status_code


def add_channels(server, channels):
    # Adds if any extra channels are found...
    #
    channels = [
        '#'+channel if not channel.startswith('#') else channel for channel in channels]

    client = next(
        client for client in Main_Bot.clients if client.server == server)

    unique = set(client.channels + channels)
    client.channels = list(unique)

    with DB_Session() as session:
        session.query(AddedServers).\
            filter(AddedServers.server == client.server).\
            update({
                "channels": client.channels
            })


def remove_channels(server, channels):
    # Removes given channels...
    #
    channels = [
        '#'+channel if not channel.startswith('#') else channel for channel in channels]

    client = next(
        client for client in Main_Bot.clients if client.server == server)

    new_channels_list = set(client.channels) - set(channels)
    client.channels = list(new_channels_list)
    with DB_Session() as session:
        session.query(AddedServers).\
            filter(AddedServers.server == client.server).\
            update({
                "channels": client.channels
            })


def add_and_connect_server(result):
    # Creates a client fron given data...
    # Server name and channels are required...
    server = result.get('server')
    channels = result.get('channels')
    port = result.get('port', 6667)

    nick = result.get('nick', None)
    user = result.get('user', None)
    real = result.get('real', None)
    port = result.get('port', 6667)

    channels = [
        '#'+channel if not channel.startswith('#') else channel for channel in channels]

    new_server = AddedServers(server=server, port=port,
                              channels=channels, on_instance=get_instance_address())

    client = Main_Bot.create_connection()
    client.connect(server, channels, port=port,
                   nick=nick, user=user, real=real)

    with DB_Session() as session:
        session.add(new_server)
    return 'Added server'


def get_instance_address():
    # Gets the instance ip address...
    ip = socket.gethostbyname(socket.gethostname())
    return '{}:{}'.format(ip, PORT)


def check_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        payload = request.get_json()
        if not payload:
            resp = {'message': 'No json data found in request.'}
            return jsonify(resp)

        return f(*args, **kws)
    return decorated_func


def varify_server_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        try:
            payload = request.get_json()
            result = ServerSchema().load(payload)
        except ValidationError as err:
            resp = {'message': err.messages}
            return jsonify(resp)

        return f(*args, **kws)
    return decorated_func


def on_instance(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        payload = request.get_json()
        result = ServerSchema().load(payload)

        with DB_Session() as session:
            match = session.query(AddedServers).\
                filter(AddedServers.server == result['server']).\
                first()
            session.expunge_all()

        if match and not match.on_instance == get_instance_address():
            address = match.on_instance + request.path
            method = request.method.lower()

            resp = redirect_req(address, method, json.dumps(payload))
            return jsonify(resp)

        return f(*args, **kws)
    return decorated_func


class Server(Resource):

    def get(self):
        server_schema = AddedServersSchema()

        with DB_Session() as session:
            servers = session.query(AddedServers)

        payload = []
        for server in servers:
            data = server_schema.dump(server)
            payload.append(data)

        return jsonify({'Data': payload})

    @check_payload
    @varify_server_payload
    @on_instance
    def post(self, *args, **kws):
        payload = request.get_json()
        result = ServerSchema().load(payload)

        with DB_Session() as session:
            match = session.query(AddedServers).\
                filter(AddedServers.server == result['server']).\
                first()

        if match:
            # Adding new channels if not already there...
            add_channels(result['server'], result['channels'])
            msg = {"message": "Server already exists. The new channels were added."}
            return jsonify(msg)
        else:
            # else the server is created and connected...
            message = add_and_connect_server(result)
            return jsonify({"message": message})

    @check_payload
    @varify_server_payload
    @on_instance
    def delete(self):
        payload = request.get_json()
        result = ServerSchema().load(payload)

        with DB_Session() as session:
            match = session.query(AddedServers).\
                filter(AddedServers.server == result['server']).\
                first()

            if not match:
                msg = {"message": "No such server."}
                return jsonify(msg)

            # Found on instance. Removing server...
            client = next(
                client for client in Main_Bot.clients if client.server == result['server'])


            Main_Bot.remove_client(client)
            session.delete(match)

            msg = {"message": "Server disconnected and removed"}
            return jsonify(msg)


def varify_channel_payload(f):
    @wraps(f)
    def decorated_func(*args, **kws):
        try:
            payload = request.get_json()
            result = ChannelSchema().load(payload)
        except ValidationError as err:
            resp = {'message': err.messages}
            return jsonify(resp)

        return f(*args, **kws)
    return decorated_func


class Channel(Resource):

    @check_payload
    @varify_channel_payload
    @on_instance
    def post(self):
        payload = request.get_json()
        result = ServerSchema().load(payload)

        with DB_Session() as session:
            match = session.query(AddedServers).\
                filter(AddedServers.server == result['server']).\
                first()

        if match:
            # add to the channels list if any channel is disconnected
            add_channels(result['server'], result['channels'])
            msg = {"message": "The new channels were added.", }
            return jsonify(msg)
        else:
            add_and_connect_server(result)
            msg = {
                "message": 'Server was not Found. Connected to server and joined channel.'}
            return jsonify(msg)

    @check_payload
    @varify_channel_payload
    @on_instance
    def delete(self):
        payload = request.get_json()
        result = ServerSchema().load(payload)

        with DB_Session() as session:
            match = session.query(AddedServers).\
                filter(AddedServers.server == result['server']).\
                first()

        if match:
            # removed the provided channels
            remove_channels(result['server'], result['channels'])
            msg = {"message": "The channels were removed.", }
            return jsonify(msg)
        else:
            msg = {"message": "No such server..", }
            return jsonify(msg)


api.add_resource(Server, '/server')
api.add_resource(Channel, '/channel')

if __name__ == '__main__':
    IRC_Bot_thread.start()
    app.run(host='0.0.0.0', port=PORT, debug=True)
