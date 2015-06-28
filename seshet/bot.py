"""Implement SeshetBot as subclass of ircutils3.bot.SimpleBot."""

import os
import sys
import traceback
from io import StringIO
from datetime import datetime

from ircutils3 import bot, client

from . import core
from .utils import KVStore, Storage


class SeshetBot(bot.SimpleBot):
    """Extend `ircutils3.bot.SimpleBot`.
    
    Each instance represents one bot, connected to one IRC network.
    Each instance should have its own database, but can make use of
    any shared command modules. The modules may have to be added to
    the bot's database if the bot wasn't created using the
    `seshet --config` or `seshet --new` commands.
    """
    
    session = Storage()
    """Shared runtime storage available for all command modules."""
    
    storage = None
    """If bot is initialized with a database connection, persistent
    KV store available for all command modules. Each module will have
    its own namespace.
    """
    
    def __init__(self, *args, **kwargs):
        """Extend `ircutils3.bot.SimpleBot.__init__()`.
        
        Keyword argument `db` is required for running commands other
        than core commands and should be an instance of pydal.DAL.
        """
        
        bot.SimpleBot.__init__(self, *args, **kwargs)
        
        if 'db' not in kwargs:
            # no database connection, only log to file and run
            # core command modules
            self._log = self._log_to_file
            self._run_commands = self._run_only_core
            
            # dummy KV store since no db
            self.storage = Storage()
        else:
            self.db = db
            self.storage = KVStore(db)
        
        # our own on_quit() handler removes users after logging their disconnect
        self.events['quit'].remove_handler(client._remove_channel_user_on_quit)
        
    def log(self, etype, source, msg='', target='', hostmask='', parms=''):
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
                                 event_time=datetime.today(),
                                 source=source,
                                 target=target,
                                 message=msg,
                                 host=hostmask,
                                 parms=parms,
                                 )
        self.db.commit()
        
    def on_message(self, e):
        self.log('PRIVMSG', e.source, e.target)
        self._run_commands(e)
    
    def on_join(self, e):
        self.log('JOIN', e.source, '', e.target, e.user+'@'+e.host)
        self._run_commands(e)
    
    def on_part(self, e):
        pass
    
    def on_quit(self, e):
        pass
    
    def on_disconnect(self, e):
        pass
    
    def on_kick(self, e):
        pass
    
    def on_nick_change(self, e):
        pass
    
    def on_ctcp_action(self, e):
        pass
    
    def on_welcome(self, e):
        pass
    
    def on_mode(self, e):
        pass
    
    def _remove_user(self, e):
        pass
    
    def _log_to_file(self, *args, **kwargs):
        """Override `log()` if bot is not initialized with a database
        connection. Do not call this method directly.
        """
        pass
    
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