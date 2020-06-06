
import cmd2
import json
from cmd2.ansi import style
from scripts.prompt.utils import *
from scripts.db.models import Download
from scripts.prompt.inquirers.connect import connect_inquirer
from scripts.prompt.inquirers.channel import channel_inquirer
from scripts.prompt.inquirers.dcc import dcc_inquirer
from scripts.prompt.inquirers.disconnect import disconnect_inquirer



class IRC_Prompt(cmd2.Cmd):
    """A simple cmd2 application."""

    def __init__(self):
        shortcuts = cmd2.DEFAULT_SHORTCUTS
        shortcuts.update({'clear': '!clear'})
        super().__init__(shortcuts=shortcuts)

        self.prompt = style("Irc-Bot #~ ", fg='bright_green', bold=True)
        self.persistent_history_file = "command_history.txt"

        self.error_color = 'red'       


    # @cmd2.with_argparser(connect_parser)
    def do_connect(self, args):
        """Connects to server."""

        connect_info = connect_inquirer()
        connect_and_save(connect_info)

        self.poutput(style("[+] Process complete.", fg='bright_magenta'))

    def do_channel(self, args):
        "Adds or removes channels.."

        try:
            payload = channel_inquirer()
            action = payload['action']

            if action == 'add':
                add_channels(payload)
            else:
                remove_channels(payload)
        except IndexError:
            self.poutput(style("[+] No server connected. Connect to server first", fg='bright_red'))
            return

    
    def do_disconnect(self, args):
        "Disconnect from server"

        try:
            payload = disconnect_inquirer() 

            if payload.get('disconnect', False):
                server = payload['server']
                client = Main_Bot.client_hash_table[server]

                Main_Bot.remove_client(client)
                # AddedServers.delete_server(server)

                self.poutput(style("[+] Server Removed.", fg='bright_magenta'))
        except:
            self.poutput(style("[+] No server connected.", fg='bright_red'))
            return

    
    def do_status(self, args):
        payload = Main_Bot.clients_status()
        self.poutput(style(json.dumps(payload, indent=4), fg='bright_magenta'))


    def do_download(self, args):
        
        try:
            payload = dcc_inquirer()

            # new_download = Download(payload['server'], payload['channel'], 
            #                         payload['target'], payload['file_name'])
            # new_download.save_to_db()
            # print('saved to db')
                        
            server = payload['server']

            client = Main_Bot.client_hash_table[server]
            client.xdcc_request(payload['target'], payload['file_name'])

            self.poutput(style("[+] Process complete.", fg='bright_magenta'))
            
        except IndexError:
            self.poutput(style("[+] No server connected.", fg='bright_red'))
            return

    def do_ss(self, args):
        connect_and_save({
            "server": "irc.openjoke.org",
            "nick": "mahirr",
            "channels": "#INTERSECT"
        })

    def do_dd(self, args):
        client = Main_Bot.client_hash_table['irc.openjoke.org']
        client.xdcc_request('SEcT|MuSiC|01', '#527')


# irc.abjects.net
# 
# server name 
# channel name
# recriver
# filename or slot 
# 
# 
# 
# 
# 
