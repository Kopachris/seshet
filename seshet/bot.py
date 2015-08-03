"""Implement SeshetBot as subclass of ircutils3.bot.SimpleBot."""

import os
import sys
import traceback
import re
from io import StringIO
from datetime import datetime
from collections import namedtuple

from ircutils3 import bot, client

from .utils import KVStore, Storage, CaselessDictionary, IRCstr


SeshetUser = namedtuple('SeshetUser', ['nick', 'user', 'real', 'host'])
SeshetChannel = namedtuple('SeshetChannel', ['name', 'users'])


class SeshetBot(bot.SimpleBot):
    """Extend `ircutils3.bot.SimpleBot`.
    
    Each instance represents one bot, connected to one IRC network.
    Each instance should have its own database, but can make use of
    any shared command modules. The modules may have to be added to
    the bot's database if the bot wasn't created using the
    `seshet --config` or `seshet --new` commands.
    """
    
    def __init__(self, nick='Seshet', db=None):
        """Extend `ircutils3.bot.SimpleBot.__init__()`.
        
        Keyword argument `db` is required for running commands other
        than core commands and should be an instance of pydal.DAL.
        """
        
        bot.SimpleBot.__init__(self, nick, auto_handle=False)
        
        # define defaults
        
        self.session = Storage()
        
        self.log_file = 'seshet.log'
        self.log_formats = {}
        self.locale = {}
        
        self.channels = CaselessDictionary()
        self.users = CaselessDictionary()
        
        if db is None:
            # no database connection, only log to file and run
            # core command modules
            self.log = self._log_to_file
            self.run_modules = self._run_only_core
            
            # dummy KV store since no db
            self.storage = Storage()
        else:
            self.db = db
            self.storage = KVStore(db)
        
        # Add default handlers
        self.events["any"].add_handler(client._update_client_info)
        self.events["ctcp_version"].add_handler(client._reply_to_ctcp_version)
        self.events["name_reply"].add_handler(self._add_channel_names)
        
    def log(self, etype, source, msg='', target='', hostmask='', params=''):
        """Log an event in the database.
        
        Required:
            `etype` - event type. One of 'PRIVMSG', 'QUIT', 'PART', 'ACTION',
                'NICK', 'JOIN', 'MODE', 'KICK', 'CTCP', or 'ERROR'. Enforced 
                by database model.
            `source` - source of the event. Usually a user. For NICK events,
                the user's original nickname. For ERROR events, this should be
                the exception name, the module name, and the line number. The
                full traceback will be logged in `msg`.
        Optional:
            `msg` - a message associated with the event.
            `target` - the target the message was directed to. For MODE and KICK
                events, this will be the user the event was performed on. For
                NICK events, this will be channel the event was seen in (an event
                will be created for each channel the user is seen by the bot in).
            `hostmask` - a hostmask associated with the event.
            `parms` - any additional parameters associated with the event, such as
                a new nickname (for NICK events), mode switches (for MODE events),
                or a dump of local variables (for ERROR events).
        """
        
        self.db.event_log.insert(event_type=etype,
                                 event_time=datetime.utcnow(),
                                 source=source,
                                 target=target,
                                 message=msg,
                                 host=hostmask,
                                 params=params,
                                 )
        self.db.commit()
        
    def run_modules(self, e):
        pass
    
    def on_message(self, e):
        self.log('privmsg',
                 source=e.source,
                 msg=e.message,
                 target=e.target,
                 )
        self.run_modules(e)
    
    def on_join(self, e):
        self.log('join',
                 source=e.source,
                 target=e.target,
                 hostmask=e.user+'@'+e.host,
                 )
        self.run_modules(e)
    
    def on_part(self, e):
        self.log('part',
                 source=e.source,
                 hostmask=e.user+'@'+e.host,
                 msg=' '.join(e.params[1:]),
                 target=e.target,
                 )
    
    def on_quit(self, e):
        for chan in self.channels.values():
            if e.source in chan.user_list:
                self.log('quit',
                         source=e.source,
                         hostmask=e.user+'@'+e.host,
                         msg=' '.join(e.params),
                         target=chan.name,
                         )
    
    def on_disconnect(self, e):
        pass
    
    def on_kick(self, e):
        self.log('kick',
                 source=e.source,
                 target=e.target,
                 params=e.params[0],
                 msg=' '.join(e.params[1:]),
                 hostmask=e.user+'@'+e.host,
                 )
    
    def on_nick_change(self, e):
        for chan in self.channels.values():
            if e.source in chan.user_list:
                self.log('nick',
                         source=e.source,
                         hostmask=e.user+'@'+e.host,
                         target=chan.name,
                         params=e.target,
                         )
    
    def on_ctcp_action(self, e):
        self.log('action',
                 source=e.source,
                 target=e.target,
                 msg=' '.join(e.params),
                 )
    
    def on_welcome(self, e):
        pass
    
    def on_mode(self, e):
        self.log('mode',
                 source=e.source,
                 msg=' '.join(e.params),
                 target=e.target,
                 )
    
    def before_poll(self):
        """Called each loop before polling sockets for I/O."""
        pass
    
    def after_poll(self):
        """Called each loop after polling sockets for I/O and
        handling any queued events.
        """
        pass
    
    def connect(self, *args, **kwargs):
        """Extend `client.SimpleClient.connect()` with defaults"""
        defaults = {}

        for i, k in enumerate(('host', 'port', 'channel', 'use_ssl', 'password')):
            if i < len(args):
                defaults[k] = args[i]
            elif k in kwargs:
                defaults[k] = kwargs[k]
            else:
                def_k = 'default_' + k
                defaults[k] = getattr(self, def_k, None)

        if defaults['use_ssl'] is None:
            defaults['use_ssl'] = False

        if defaults['host'] is None:
            raise TypeError("missing 1 required positional argument: 'host'")

        client.SimpleClient.connect(self, **defaults)

    def start(self):
        self._loop(self.conn._map)
        
    def _add_channel_names(self, e):
        pass
    
    def _remove_user(self, e):
        pass
    
    def _log_to_file(self, etype, source, msg='', target='', hostmask='', params=''):
        """Override `log()` if bot is not initialized with a database
        connection. Do not call this method directly.
        """
        today = datetime.utcnow()
        # TODO: Use self.locale['timezone'] for changing time
        date = today.strftime(self.locale['date_fmt'])
        time = today.strftime(self.locale['time_fmt'])
        datetime_s = today.strftime(self.locale['short_datetime_fmt'])
        datetime_l = today.strftime(self.locale['long_datetime_fmt'])
        
        if target == self.nickname and etype in ('privmsg', 'action'):
            target = source

        if etype in self.log_formats:
            file_path = os.path.expanduser(self.log_file.format(**locals()))
            file_dir = os.path.dirname(file_path)
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)

            line = self.log_formats[etype].format(**locals())
            with open(file_path, 'a') as log:
                log.write(line+'\n')
        # else do nothing
    
    def _run_only_core(self, *args, **kwargs):
        """Override `_run_commands()` if bot is not initialized with a
        database connection. Do not call this method directly.
        
        Rather than getting a list of enabled modules from the database,
        Seshet will only run the commands defined by `core` in this package.
        The bot will only run commands given in private message ("query")
        by either an authenticated user defined in the instance's config file,
        or by any user with the same hostmask if authentication isn't set up
        in the instance's config file.
        
        The `core` command module from this package can only be overridden if
        the bot is initialized with a database connection and a new `core`
        module is entered into the database.
        """
        pass

    def _loop(self, map):
        """The main loop. Poll sockets for I/O and run any other functions
        that need to be run every loop.
        """
        try:
            from asyncore import poll
        except ImportError:
            raise Exception("Couldn't find poll function. Cannot start bot.")
    
        while map:
            self.before_poll()
            poll(timeout=30.0, map=map)
            self.after_poll()
