seshet
======

Modular, dynamic Python IRC bot


Installing
----------

Simply clone the repository and run ``./setup.py install``. You may need to mark it as executable first, and may need to run it as root or with sudo.

You can also install using ``pip3 install seshet``.

Running
-------

After isntalling, you can test that the installed version works by running ``seshet-test.py`` or by opening a Python 3 interpreter and running::

    >>> import seshet.config
    >>> bot = seshet.config.build_bot()
    >>> bot.connect()
    >>> bot.start()
    
This will start a bot using the default configuration. You can terminate the bot at any time by terminating the Python interpreter.

Note: ``seshet-test.py`` does not use a database, but creates a log file ``./seshet.log``. Importing seshet and building a bot using the default configuration as described above does use a database and creates a ``./seshet.db`` file and some ``./*.table`` files.
