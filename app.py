#!/usr/bin/python3
import configparser
import scripts.irc as IRC

if __name__ == "__main__": 

    parser = configparser.ConfigParser()
    irc_obj = IRC.IRC_Object()

    try:
        with open('conf.ini') as f:
            parser.read_file(f)
    except IOError:
        raise Exception("There is no config file..")

    nick = parser.get("User_Info", "Nick_Name", fallback="sucker")
    user = parser.get("User_Info", "User_Name", fallback="mahir")
    real = parser.get("User_Info", "Real_Name", fallback="Mahir Ashab")
    
    if not (nick and user and real):
        raise Exception("Invalid User Credentials...")

    if not parser.sections()[1:]:
        raise Exception("NO SERVERS GIVEN...")


    for server_section in parser.sections()[1:]:
        s_name = parser.get(server_section, "Address")
        s_port = parser.get(server_section, "Port")
        s_channels = parser.get(server_section, "Chnnels").split(",")

        s_channels = list(filter(lambda x: x != '', s_channels))

        if not s_port.isdigit or s_port == '': 
            print("Invalid Port. Server not created.")
            continue
        else:
            s_port = int(s_port)


        if s_name and s_port and s_channels:
            client = irc_obj.create_connection()
            client.connect(s_name, s_port, s_channels, nick, user, real)
        else:
            print("Invalis server args. Server not created.")
            

    irc_obj.process_all_connections()
    