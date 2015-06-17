"""Implement SeshetBot as subclass of ircutils.bot.SimpleBot."""

import os
import sys
import traceback
from io import StringIO

from ircutils import bot, client

from . import core
from .utils import KVStore, Storage


class SeshetBot(bot.SimpleBot):
    """Extend `ircutils.bot.SimpleBot`.
    
    Each instance represents one bot, connected to one IRC network.
    Each instance should have its own database, but can make use of
    any shared command modules. The modules may have to be added to
    the bot's database if the bot wasn't created using the
    `seshet --config` or `seshet --new` commands.
    """
    
    storage = Storage()
    """Shared runtime storage available for all command modules."""
    
    def __init__(self, *args, **kwargs):
        """Extend `ircutils.bot.SimpleBot.__init__()`.
        
        Keyword argument `db` is required for running commands other
        than core commands, and should be an instance of pydal.DAL.
        """
        
        bot.SimpleBot.__init__(self, *args, **kwargs)
        
        if 'db' not in kwargs:
            # no database connection, only log to file and run
            # core command modules
            self._log = self._log_to_file
            self._run_commands = self._run_only_core
        else:
            self.db = db
        
        # our own on_quit() handler removes users after logging their disconnect
        self.events['quit'].remove_handler(client._remove_channel_user_on_quit)
        
    def _log_to_file(self, *args, **kwargs):
        """Override `_log()` if bot is not initialized with a database
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