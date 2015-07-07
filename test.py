#!/usr/bin/env python3

from seshet.bot import SeshetBot
from pydal import DAL, Field
from datetime import datetime

def main():
    print("Opening database...")
    db = DAL('sqlite://seshet.db')
    print("Defining database table...")
    db.define_table('event_log',
                    Field('event_time', 'datetime', default=datetime.today()),
                    Field('event_type', 'string'),
                    Field('source', 'string'),
                    Field('target', 'string'),
                    Field('message', 'string'),
                    Field('host', 'string'),
                    Field('parms', 'string'),
                    )
    
    print("\tDatabase OK.\nInitializing bot...")
    bot = SeshetBot('SeshetBot', db=db)
    bot.user = 'SeshetBot'
    bot.real_name = 'SeshetBot'
    
    print("Connecting...", end=' ')
    bot.connect('irc.esper.net', channel='#hard-light')
    print("Connected.\nStarting main loop...")
    bot.start()

if __name__ == '__main__':
    main()