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
privmsg: [{time}] <{source}> {msg}
join: [{time}] -- {source} ({hostmask}) has joined
part: [{time}] -- {source} ({hostmask}) has left ({msg})
quit: [{time}] -- {source} ({hostmask}) has quit ({msg})
kick: [{time}] -- {target} ({hostmask}) has been kicked by {source} ({msg})
mode: [{time}] -- {source} ({hostmask}) has set mode {parms} on {target}
nick: [{time}] -- {source} is now known as {parms}
action: [{time}] * {source} {msg}

[debug]
use_debug: False
# corresponds to levels in logging module
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
file: ~/.seshet/logs/{target}_{date}.log
privmsg: [{time}] <{source}> {msg}
join: [{time}] -- {source} ({hostmask}) has joined
part: [{time}] -- {source} ({hostmask}) has left ({msg})
quit: [{time}] -- {source} ({hostmask}) has quit ({msg})
kick: [{time}] -- {params} has been kicked by {source} ({msg})
mode: [{time}] -- {source} ({hostmask}) has set mode {msg} on {target}
nick: [{time}] -- {source} is now known as {params}
action: [{time}] * {source} {msg}

[debug]
# corresponds to levels in logging module
verbosity: debug
file: ~/.seshet/logs/debug.log
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
                    Field('params', 'list:string'),
                    )
    db.define_table('modules',
                    Field('name', notnull=True, unique=True, length=256),
                    Field('enabled', 'boolean'),
                    Field('event_types', 'list:string'),
                    Field('description', 'text'),
                    Field('echannels', 'list:string'),
                    Field('dchannels', 'list:string'),
                    Field('enicks', 'list:string'),
                    Field('dnicks', 'list:string'),
                    Field('whitelist', 'list:string'),
                    Field('blacklist', 'list:string'),
                    Field('cmd_prefix', length=1, default='!'),
                    Field('acl', 'json'),
                    Field('rate_limit', 'json'),
                    )
        

def build_bot(config_file=None):
    """Parse a config and return a SeshetBot instance. After, the bot can be run
    simply by calling .connect() and then .start()
    
    Optional arguments:
        config_file - valid file path or ConfigParser instance
        
        If config_file is None, will read default config defined in this module.
    """
    
    from . import bot

    config = ConfigParser(interpolation=None)
    if config_file is None:
        config.read_string(default_config)
    elif isinstance(config_file, ConfigParser):
        config = config_file
    else:
        config.read(config_file)

    verbosity = config['debug']['verbosity'].lower()
    seshetbot.log_verbosity = int(debug_lvls[verbosity])
    seshetbot.debug_file = config['debug']['file']
    
    # shorter names
    db_conf = config['database']
    conn_conf = config['connection']
    client_conf = config['client']
    log_conf = config['logging']
    verbosity = config['debug']['verbosity'].lower() or 'notset'
    debug_file = config['debug']['file'] or None
    # add more as they're used

    if db_conf.getboolean('use_db'):
        db = DAL(db_conf['db_string'])
        build_db_tables(db)
        log_file = None
        log_fmts = {}
    else:
        db = None
        log_file = log_conf.pop('file')
        log_fmts = dict(log_conf)
        
    # debug logging
    debug_lvls = {'notset': 0,
                  'debug': 10,
                  'info': 20,
                  'warning': 30,
                  'error': 40,
                  'critical': 50,
                  }
    lvl = int(debug_lvls[verbosity])
    
    seshetbot = bot.SeshetBot(client_conf['nickname'], db, debug_file, lvl)

    # connection info for connect()
    seshetbot.default_host = conn_conf['server']
    seshetbot.default_port = int(conn_conf['port'])
    seshetbot.default_channel = conn_conf['channels'].split(',')
    seshetbot.default_use_ssl = conn_conf.getboolean('ssl')

    # client info
    seshetbot.user = client_conf['user']
    seshetbot.real_name = client_conf['realname']

    # logging info
    seshetbot.log_file = log_file
    seshetbot.log_formats = log_fmts
    seshetbot.locale = dict(config['locale'])
    
    return seshetbot