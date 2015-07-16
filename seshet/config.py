"""Define default configuration, read configuration file, and apply
configuration to SeshetBot instance.
"""

from configparser import ConfigParser

from pydal import DAL, Field


default_config = """
[connection]
# passed to SeshetBot.connect()
server: chat.freenode.net
port: 6667
channels: #botwar
ssl: False

[client]
nickname: Seshet
user: seshet
realname: seshetbot

[welcome]
# stuff sent by the bot after connecting
use_nickserv: False
nickserv_pass:
user_mode: -x

[locale]
timezone: UTC
locale: en_US
# see docs for datetime.strftime
date_fmt: %m%d%y
# 071415
time_fmt: %H:%M:%S
# 11:49:57
short_datetime_fmt: %Y-%m-%d %H:%M:%S
# 2015-07-14 11:49:57
long_datetime_fmt: %A %d %B %Y at %H:%M:%S %Z
# Tuesday 14 July 2015 at 11:49:57 UTC

[database]
use_db: True
db_string: sqlite://seshet.db

[logging]
# if using db, this will be ignored
file: logs/%(target)s_%(date)s.log

[debug]
# corresponds to levels in logging module or None
verbosity: warning
file: seshet-debug.log
"""


testing_config = """
[connection]
# passed to SeshetBot.connect()
server: chat.freenode.net
port: 6667
channels: #botwar
ssl: False

[client]
nickname: Seshet
user: seshet
realname: seshetbot

[welcome]
# stuff sent by the bot after connecting
use_nickserv: False
nickserv_pass:
user_mode: -x

[locale]
timezone: UTC
locale: en_US
# see docs for datetime.strftime
date_fmt: %m%d%y
# 071415
time_fmt: %H:%M:%S
# 11:49:57
short_datetime_fmt: %Y-%m-%d %H:%M:%S
# 2015-07-14 11:49:57
long_datetime_fmt: %A %d %B %Y at %H:%M:%S %Z
# Tuesday 14 July 2015 at 11:49:57 UTC

[database]
# no db connection for testing
use_db: False

[logging]
# if using db, this will be ignored
file: logs/%(target)s_%(date)s.log

[debug]
# corresponds to levels in logging module or None
verbosity: debug
file: seshet-debug.log
"""


def build_db_tables(db):
    """Build Seshet's basic database schema. Requires one parameter,
    `db` as `pydal.DAL` instance.
    """
    if not isinstance(db, DAL) or not db._uri:
        raise Exception("Need valid DAL object to define tables")

    # event log - self-explanatory, logs all events
    db.define_table('event_log',
                    Field('event_type'),
                    Field('event_time', 'datetime'),
                    Field('source'),
                    Field('target'),
                    Field('message', 'text'),
                    Field('host'),
                    Field('parms', 'list:string'),
                    )
        

def build_bot(config_file=None):
    """Parse a config and return a SeshetBot instance. After, the bot can be run
    simply by calling .connect() and then .start()
    
    Optional arguments:
        config_file - valid file path or ConfigParser instance
        
        If config_file is None, will read default config defined in this module.
    """
    from . import bot

    config = ConfigParser()
    if config_file is None:
        config.read_string(default_config)
    elif isinstance(config_file, ConfigParser):
        config = config_file
    else:
        config.read(config_file)

    # shorter names
    db_conf = config['database']
    conn_conf = config['connection']
    client_conf = config['client']
    # add more as they're used

    if db_conf.getboolean('use_db'):
        db = DAL(db_conf['db_string'])
        build_db_tables(db)
    else:
        db = None

    seshetbot = bot.SeshetBot(client_conf['nickname'], db)

    # connection info for connect()
    seshetbot.default_host = conn_conf['server']
    seshetbot.default_port = int(conn_conf['port'])
    seshetbot.default_channel = conn_conf['channels'].split(',')
    seshetbot.default_use_ssl = conn_conf.getboolean('ssl')

    # client info
    seshetbot.user = client_conf['user']
    seshetbot.real_name = client_conf['realname']

    return seshetbot