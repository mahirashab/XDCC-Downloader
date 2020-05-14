#!./.env/bin/python3

import os
import json
import socket
import logging
import requests
import threading
import http.client
import scripts.db.database as db

from scripts.bot import irc
from marshmallow import ValidationError
from scripts.db.models import AddedServers
from flask import Flask, request, jsonify
from scripts.db.schema import ServerSchema, ChannelSchema, AddedServersSchema

activity_logger = logging.getLogger("ActivityLogger")

Main_Bot = irc.IRC_Bot_Object()
IRC_Bot_thread = threading.Thread(target=Main_Bot.run, daemon=True)
db.init_db()

DB_Session = db.Session
PORT = 5000

nick = os.environ.get('NICK_NAME')
user = os.environ.get('USER_NAME')
real = os.environ.get('REAL_NAME')


app = Flask(__name__)

@app.route('/server', methods=['POST', 'GET', 'DELETE'])
def server_handler():
    # This sqlalchemy session is only used in the scope of this func
    session = DB_Session()
    # If a get request is sent, all the servers info in AddedServers are returned
    if request.method == 'GET':
        server_schema = AddedServersSchema()
        servers = session.query(AddedServers)
        payload = []
        for server in servers:
            data = server_schema.dump(server)
            payload.append(data)

        return  jsonify({'Data': payload}), http.client.OK
    
    # If request is post or delete. 
    # This checks if the payload is not empty
    payload = request.get_json()
    if not payload:
        resp = {'message': 'No json data found in request.'}
        return jsonify(resp), http.client.BAD_REQUEST

    # main error handler
    try:
        # Validating if appropriate data was sent
        result = ServerSchema().load(payload)
        match = session.query(AddedServers).\
                    filter(AddedServers.server==result['server']).\
                    first()

        # if the method is delete. the server is deleted and disconnected.
        if request.method == 'DELETE':
            if not match: return 'No such server'

            # If the connection is on this instance
            if match.on_instance == get_instance_address():
                # Found on instance. Removing server...
                conn = list(filter(lambda conn: conn.server == result['server'], Main_Bot.connections))[0]
                Main_Bot.remove_connection(conn)
                session.delete(match)
                session.commit()
                session.close()
                msg = { "message": "Server disconnected and removed", }
                return jsonify(msg), http.client.OK
            else:
                # Sending request to instance server...
                resp = redirect_req(match.on_instance + '/server', 'delete', json.dumps(payload))
                return jsonify(resp), http.client.OK

        # Runs if the request is post
        # if server is present, extra channels are joined.
        if match:
            if match.on_instance == get_instance_address():
                # Adding new channels if not already there...
                add_channels(result['server'], result['channels'])
                msg = { "message": "Server already exists. The new channels were added.", }
                return jsonify(msg), http.client.OK
            else:
                # Sending request to instance server...
                resp = redirect_req(match.on_instance + '/server', 'post', json.dumps(payload))
                return jsonify(resp), http.client.OK
        else:
            # else the server is created and connected...
            message = add_and_connect_server(result, session)
            return jsonify({"message": message}), http.client.OK
        
    except ValidationError as err:
        resp = { 'message': err.messages }
        return jsonify(resp), http.client.BAD_REQUEST
    except KeyError as err:
        resp = { 'message': 'Proper keys are not sent.'}
        return jsonify(resp), http.client.BAD_REQUEST


@app.route('/channel', methods=['POST'])
def channel_handler():
    session = DB_Session()
    # checking if payload is given
    payload = request.get_json()
    if not payload:
        resp = {'message': 'No json data found in request.'}
        return jsonify(resp), http.client.BAD_REQUEST

    try:
        # getting the server
        result = ChannelSchema().load(payload)
        match = session.query(AddedServers).\
                filter(AddedServers.server==result['server']).\
                first()

        if match:
            # The extra channels are joined..
            if match.on_instance == get_instance_address():
                # add to the channels list if any channel is disconnected
                add_channels(result['server'], result['channels'])
                msg = { "message": "The new channels were added.", }
                return jsonify(msg), http.client.OK
            else:
                resp = redirect_req(match.on_instance + '/channel', 'post', json.dumps(payload))
                return jsonify(resp), http.client.OK
        # else the server is connected to default port and the channels are joined...
        else:
            add_and_connect_server(result, session, port=True)
            return jsonify({"message": 'Server was not connected. Connected to server and joined channel.'}), http.client.OK

    except ValidationError as err:
        resp = { 'message': err.messages }
        return jsonify(resp), http.client.BAD_REQUEST
    except KeyError as err:
        resp = { 'message': 'Proper keys are not sent.'}
        return jsonify(resp), http.client.BAD_REQUEST


@app.route('/help')
def get_help():
    resp = {
        "message": 'This describes the full api..',
        "API": {
            "/server" : {
                "method:post": {
                    "payload" : {
                        "server": 'server name (str)',
                        "port": 'port number (int)',
                        "channels": 'list of channels (str)'
                    },
                    "action": 'Adds the server to db. Connects to it. Joins channels.'
                },
                "method:get": {
                    "action" : 'sends all the connections data back..'
                },
                "method:delete": {
                    "payload": {
                        "server": 'server name'
                    },
                    "action": 'deletes the server.'
                }
            },
            "/channel": {
                "method:post": {
                    "payload": {
                        "server": 'server name (str)',
                        "channels": 'list of channel names (str)'
                    },
                    "action": 'adds the channels to server.'
                }
            }
        }
    }

    return jsonify(resp), http.client.OK


'''Sends request to the connection host instance...'''
def redirect_req(url, method, payload):
    url = 'http://' + url
    method = method.lower()
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    if method == 'post':
        response = requests.post(url, headers=headers, data=payload)
    elif method == 'delete':
        response = requests.delete(url, headers=headers, data=payload)

    return response.json(), response.status_code

    
'''Adds if any extra channels are found...'''
def add_channels(server, channels):
    conn = list(filter(lambda conn: conn.server == server, Main_Bot.connections))[0]
    unique = set(conn.channels + channels)
    conn.channels = list(unique)


'''Creates new server in db. and connects to it..'''
def add_and_connect_server(result, session, port=False):
    if port:
        result['port'] = 6667

    new_server = AddedServers(server=result['server'], port=result['port'], channels=result['channels'], on_instance=get_instance_address())

    client = Main_Bot.create_connection()
    client.connect(result["server"], result["port"], result["channels"], nick, user, real, db.session)

    session.add(new_server)
    session.commit()
    session.close()
    return 'Added server'


'''This gets the instance address..'''
def get_instance_address():
    ip = socket.gethostbyname(socket.gethostname())
    return f'{ip}:{PORT}'


if __name__ == '__main__':
    IRC_Bot_thread.start()

    activity_logger.info('Starting the main background checking thread thread..')
    Main_Bot.update_connection_status(db.Session)

    activity_logger.info('Starting flask app on port %d', PORT)
    app.run(host='0.0.0.0', port=PORT, debug=True)