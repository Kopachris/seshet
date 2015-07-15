"""Implement SeshetBot as subclass of ircutils3.bot.SimpleBot."""

import os
import sys
import traceback
from io import StringIO
from datetime import datetime

from ircutils3 import bot, client

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
    
    def __init__(self, nick='Seshet', db=None):
        """Extend `ircutils3.bot.SimpleBot.__init__()`.
        
        Keyword argument `db` is required for running commands other
        than core commands and should be an instance of pydal.DAL.
        """
        
        bot.SimpleBot.__init__(self, nick, auto_handle=False)
        
        if db is None:
            # no database connection, only log to file and run
            # core command modules
            self.log = self._log_to_file
            self.run_commands = self._run_only_core
            
            # dummy KV store since no db
            self.storage = Storage()
        else:
            self.db = db
            self.storage = KVStore(db)
        
        # Add default handlers
        self.events["any"].add_handler(client._update_client_info)
        self.events["ctcp_version"].add_handler(client._reply_to_ctcp_version)
        
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
        
    def run_commands(self, e):
        pass
    
    def on_message(self, e):
        self.log('PRIVMSG', e.source, e.message, e.target)
        self.run_commands(e)
    
    def on_join(self, e):
        self.log('JOIN', e.source, '', e.target, e.user+'@'+e.host)
        self.run_commands(e)
    
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
        # will be changed
        self.log('MODE', e.source, str(e.params), e.target)
    
    def before_poll(self):
        """Called each loop before polling sockets for I/O."""
        pass
    
    def after_poll(self):
        """Called each loop after polling sockets for I/O and
        handling any queued events.
        """
        pass
    
    def start(self):
        self._loop(self.conn._map)
    
    def _remove_user(self, e):
        pass
    
    def _log_to_file(self, etype, source, msg='', target='', hostmask='', parms=''):
        """Override `log()` if bot is not initialized with a database
        connection. Do not call this method directly.
        """
        if etype == 'PRIVMSG':
            log = open('seshet.log', 'a')
            log.write("<{}> {}\n".format(source, msg))
            log.close()
        elif etype == 'MODE':
            log = open('seshet.log', 'a')
            log.write("{} MODE {} {}\n".format(source, target, msg))
            log.close()
    
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