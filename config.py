'''
This is the main config file. 
[[[Here]]]

(User_Info) is the dict that contains all the user info.
Nick, User and Real keys must be set...

(Servers) is a list of dict.
Every dict in the list must have the three values
Address, Port and Channels....
'''

User_Info = dict(
    Nick = "sucker", # Nickname of user
    User = "mahir", # Username 
    Real = "Mahir Ashab", # Realname of user
    Password = "",
    SSL = "",
)

Servers = [
    dict(
        Address = "irc.abjects.net", # Server address
        Port = 6667, # Server port
        Channels = ["#beast-xdcc"] # Channels to join 
    ),
    dict(
       Address = "irc.abjects.net",
        Port = 6667,
        Channels = ["#moviegods "]
    )
]


'''This function returns the user info in tuple...'''
def get_user():
    nick = User_Info.get("Nick", None)
    user = User_Info.get("User", None)
    real = User_Info.get("Real", None)
    password = User_Info.get("Password", None)
    ssl = User_Info.get("SSL", None)


    if nick and user and real:
        return (nick, user, real, password, ssl)
    else:
        raise Exception("Invalid user info...")


'''This function filters useable servers...'''
def get_servers():
    valid_servers = []
    for server in Servers:
        address = server.get("Address", None)
        port = server.get("Port", None)
        channels = server.get("Channels", None)

        if address and port and channels:
            if type(port) == int and type(channels) == list:
                valid_servers.append(server)

    return valid_servers
