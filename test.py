#!/usr/bin/env python3

from seshet.bot import SeshetBot
from pydal import DAL, Field
from datetime import datetime

db = DAL('sqlite://seshet.db')
db.define_table('event_log',
                Field('event_time', 'datetime', default=datetime.today()),
                Field('event_type', 'string'),
                Field('source', 'string'),
                Field('target', 'string'),
                Field('message', 'string'),
                Field('host', 'string'),
                Field('parms', 'string'),
                )

bot = SeshetBot('SeshetBot', db=db)
bot.user = 'SeshetBot'
bot.real_name = 'SeshetBot'

bot.connect('irc.esper.net', channel='#hard-light')
bot.start()