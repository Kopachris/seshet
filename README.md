# seshet
Modular, dynamic Python IRC bot


## Installing

Simply clone the repository and run `./setup.py install`. You may need to mark it as executable first, and may need to run it as root or with `sudo`.

## Running

Without installing, you can test it by running `./test.py`. It will not use a database by default. After isntalling, you can test that the installed version works by opening a Python 3 interpreter and running:

    >>> import seshet.config
    >>> bot = seshet.config.build_bot()
    >>> bot.connect()
    >>> bot.start()
    
This will start a bot using the default configuration. You can terminate the bot at any time by terminating the Python interpreter.
