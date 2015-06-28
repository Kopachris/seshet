#!/usr/bin/env python3

from seshet.bot import SeshetBot

bot = SeshetBot('SeshetBot')
bot.user = 'SeshetBot'
bot.real_name = 'SeshetBot'

bot.connect('irc.ponychat.net', channel='#geek')
bot.start()