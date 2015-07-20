#!/usr/bin/env python3

from configparser import ConfigParser
from seshet import config

test_config = ConfigParser(interpolation=None)
test_config.read_string(config.testing_config)

nick = input("Nickname? (Seshet) ") or "Seshet"
server = input("Server? (chat.freenode.net) ") or "chat.freenode.net"
port = input("Port? (6667) ") or '6667'
channel = input("Channel to join? (#botwar) ") or "#botwar"

test_config['client']['nickname'] = nick
test_config['connection']['server'] = server
test_config['connection']['port'] = port
test_config['connection']['channels'] = channel

seshetbot = config.build_bot(test_config)

print("Connecting...", end=" ")
seshetbot.connect()
print("Done.\nPress Ctrl-C to quit.")
seshetbot.start()
