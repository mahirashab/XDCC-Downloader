#!/usr/bin/python3

import scripts.irc as IRC
import os.path as path

try:
    import config
except ImportError as err:
    raise Exception("No config file....")

def get_user_info(info):
    keys = list(info.keys())

    if "Nick_Name" and "User_Name" and "Real_Name" in keys:
        result = []
        result.append(info.get("Nick_Name"))
        result.append(info.get("User_Name"))
        result.append(info.get("Real_Name"))
        result.append(info.get("Password"))
        result.append(info.get("SSL"))

        if result[0] and result[1] and result[2]:
            return result
        else:
            raise ValueError("Empty value is user info")
            
    else:
        raise Exception("Invalid user info...")


def get_server_list(s_list):
    result = []
    for s in s_list:
        keys = list(s.keys())
        if "Address" and "Port" and "Channels" in keys:
            if type(s.get("Port")) == int and type(s.get("Channels")) == list and len(s.get("Channels")):
                result.append(s)
    return result


if __name__ == "__main__": 

    irc_obj = IRC.IRC_Object()

    nick, user, real, pswd, ssl = get_user_info(config.User_Info)

    servers = get_server_list(config.Servers)

    if servers:
        for server in servers:
            client = irc_obj.create_connection()
            client.connect(server["Address"], server["Port"], server["Channels"], nick, user, real)
     

    irc_obj.process_all_connections()
    