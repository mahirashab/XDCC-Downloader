#!/usr/bin/python3
import irc as IRC

if __name__ == "__main__": 
    irc_obj = IRC.IRC_Object()
    irc_obj.create_connection()
    irc_obj.process_all_connections()
    