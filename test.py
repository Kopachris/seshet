#!/usr/bin/env python3

from seshet import bot

nick = input("Nickname? (Seshet) ") or "Seshet"
server = input("Server? (chat.freenode.net) ") or "chat.freenode.net"
port = input("Port? (6667) ") or 6667
channel = input("Channel to join? (#botwar) ") or "#botwar"

seshetbot = bot.SeshetBot(nick)

print("Connecting...", end=" ")
seshetbot.connect(server, port=int(port), channel=channel)
print("Done.\nPress Ctrl-C to quit.")
seshetbot.start()