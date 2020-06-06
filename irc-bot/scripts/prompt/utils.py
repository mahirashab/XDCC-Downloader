
from cmd2.ansi import style
from scripts.bot import Main_Bot

def fixed_channels(channels):
    channels = list(filter(lambda cnl: cnl, channels))
    channels = list(map(lambda cnl: cnl.lower(), channels))
    
    return ['#' + channel 
                if not channel.startswith('#')
                else channel 
                for channel in channels]


def add_channels(payload):
    # Adds if any extra channels are found...
    #
    server, channels = payload['server'], payload['channels']
    channels = payload.get('channels').split(',')
    channels = fixed_channels(channels)

    client = Main_Bot.client_hash_table[server]

    # Set the new updated channels list...
    unique = set(client.channels + channels)
    client.channels = list(unique)


def remove_channels(payload):
    # Removes given channels...
    #
    server, channels = payload['server'], payload['channels']
    channels = payload.get('channels').split(',')
    channels = fixed_channels(channels)

    client = Main_Bot.client_hash_table[server]

    # Set the new updated channels list...
    new_channels_list = set(client.channels) - set(channels)
    client.channels = list(new_channels_list)



def connect_and_save(payload):
    # Creates a client fron given data...
    # 
    server = payload['server']# Get server name...
    channels = payload.get('channels').split(',')
    
    channels = fixed_channels(channels) # Fix the channel names...

    # Creates new client and sets hash...
    client = Main_Bot.create_client()
    Main_Bot.client_hash_table[server] = client

    # Connect the client to server...
    client.connect(server, 
            channels=channels,
            port=payload.get('port', 6667),
            nick=payload.get('nick', None),
            user=payload.get('user', None), 
            real=payload.get('real', None),
            ssl=payload.get('ssl', None),
            password=payload.get('password', None))


