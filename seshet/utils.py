"""Various utility classes used by the bot and command modules.

`Storage` is copied from gluon.storage, part of the web2py framework,
    Copyrighted by Massimo Di Pierro <mdipierro@cs.depaul.edu>,
    License: LGPLv3 (http://www.gnu.org/licenses/lgpl.html)
"""

import random
import inspect
import pickle
import string
from collections import UserString

from pydal import Field

# TODO: IRCstr should go in next version of ircutils3.protocol

irc_uppercase = string.ascii_uppercase + "[]\~"
irc_lowercase = string.ascii_lowercase + "{}|^"
upper_to_lower = str.maketrans(irc_uppercase, irc_lowercase)
lower_to_upper = str.maketrans(irc_lowercase, irc_uppercase)


class IRCstr(UserString):
    """Implement str, overriding case-changing methods to only handle ASCII
    cases plus "{}|^" and "[]\~" as defined by RFC 2812.
    
    Hashing and equality testing is case insensitive! That is, __hash__ will
    return the hash of the lowercase version of the string, and __eq__ will
    convert both operands to lowercase before testing equality.
    """
    
    def casefold(self):
        return self.lower()
        
    def lower(self):
        return self.data.translate(upper_to_lower)
    
    def upper(self):
        return self.data.translate(lower_to_upper)
    
    def islower(self):
        return self.data == self.data.lower()
    
    def isupper(self):
        return self.data == self.data.upper()
    
    def __hash__(self):
        return hash(self.data.lower())
        
    def __eq__(self, other):
        if isinstance(other, IRCstr):
            return self.data.lower() == other.lower()
        elif isinstance(other, str):
            # Use our custom lowercasing for IRC on other
            return self.data.lower() == other.translate(upper_to_lower)
        else:
            raise TypeError("Could not compare {} and {}".format(self, other))


class Storage(dict):
    """A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`, and setting obj.foo = None deletes item foo.

    Example:

        >>> o = Storage(a=1)
        >>> print o.a
        1

        >>> o['a']
        1

        >>> o.a = 2
        >>> print o['a']
        2

        >>> del o.a
        >>> print o.a
        None

    """
    
    __slots__ = ()
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    __getitem__ = dict.get
    __getattr__ = dict.get
    __getnewargs__ = lambda self: getattr(dict,self).__getnewargs__(self)
    __repr__ = lambda self: '<Storage %s>' % dict.__repr__(self)
    __getstate__ = lambda self: None
    __copy__ = lambda self: Storage(self)

    def getlist(self, key):
        """Returns a Storage value as a list.

        If the value is a list it will be returned as-is.
        If object is None, an empty list will be returned.
        Otherwise, `[value]` will be returned.

        Example output for a query string of `?x=abc&y=abc&y=def`::

            >>> request = Storage()
            >>> request.vars = Storage()
            >>> request.vars.x = 'abc'
            >>> request.vars.y = ['abc', 'def']
            >>> request.vars.getlist('x')
            ['abc']
            >>> request.vars.getlist('y')
            ['abc', 'def']
            >>> request.vars.getlist('z')
            []

        """
        
        value = self.get(key, [])
        if value is None or isinstance(value, (list, tuple)):
            return value
        else:
            return [value]

    def getfirst(self, key, default=None):
        """Returns the first value of a list or the value itself when given a
        `request.vars` style key.

        If the value is a list, its first item will be returned;
        otherwise, the value will be returned as-is.

        Example output for a query string of `?x=abc&y=abc&y=def`::

            >>> request = Storage()
            >>> request.vars = Storage()
            >>> request.vars.x = 'abc'
            >>> request.vars.y = ['abc', 'def']
            >>> request.vars.getfirst('x')
            'abc'
            >>> request.vars.getfirst('y')
            'abc'
            >>> request.vars.getfirst('z')

        """
        
        values = self.getlist(key)
        return values[0] if values else default

    def getlast(self, key, default=None):
        """Returns the last value of a list or value itself when given a
        `request.vars` style key.

        If the value is a list, the last item will be returned;
        otherwise, the value will be returned as-is.

        Simulated output with a query string of `?x=abc&y=abc&y=def`::

            >>> request = Storage()
            >>> request.vars = Storage()
            >>> request.vars.x = 'abc'
            >>> request.vars.y = ['abc', 'def']
            >>> request.vars.getlast('x')
            'abc'
            >>> request.vars.getlast('y')
            'def'
            >>> request.vars.getlast('z')

        """
        
        values = self.getlist(key)
        return values[-1] if values else default


class KVStore:
    """Create a key/value store in the bot's database for each
    command module to use for persistent storage. Can be accessed
    either like a class:
    
        >>> store = KVStore(db)
        >>> store.foo = 'bar'
        >>> store.foo
        'bar'
        
    Or like a dict:
    
        >>> store['spam'] = 'eggs'
        >>> store['spam']
        'eggs'
        
    The KVStore object uses `inspect` to determine which module
    the object is being accessed from and will automatically create
    a database table as needed or determine which one to use if it
    already exists, so that each module the object is used from has
    its own namespace.
    
    KVStore has most of the same interfaces as an ordinary `dict`, but
    is not a subclass of `dict` or `collections.UserDict` because
    so many functions had to be completely rewritten to work with
    KVStore's database model.
    """

    def __init__(self, db):
        # make sure some tables are defined:
        
        if 'namespaces' not in db:
            # list of registered modules
            db.define_table('namespaces', Field('name'))
            
        for m in db().select(db.namespaces.ALL):
            # these are modules' own "namespaces"
            tbl_name = 'kv_' + m.name
            if tbl_name not in db:
                db.define_table(tbl_name,
                                Field('k', 'string', unique=True),
                                Field('v', 'text'),
                                )
        
        self._db = db   # pydal DAL instance
        # It's recommended to use a separate database
        # for the bot and for the KV store to avoid
        # accidental or malicious name collisions
        #
        # (Then why doesn't the default implimentation?)
        
    def __getattr__(self, k):
        if k.startswith('_'):
            return self.__dict__[k]
        
        db = self._db
        
        tbl = self._get_calling_module()
        tbl_name = 'kv_' + tbl if tbl is not None else None
        if tbl is None or tbl_name not in db:
            # table doesn't exist
            return None
        
        r = db(db[tbl_name].k == k)
        if r.isempty():
            # no db entry for this key
            return None
        
        r = r.select().first()
        
        # db should return string, pickle expects bytes
        return pickle.loads(r.v.encode(errors='ignore'))

    def __setattr__(self, k, v):
        if k.startswith('_'):
            self.__dict__[k] = v
            return
        elif k in self.__dict__:
            # instance attributes should be read-only-ish
            raise AttributeError("Name already in use: %s" % k)
        
        db = self._db
        
        if v is not None:
            v = pickle.dumps(v).decode(errors='ignore')
        
        tbl = self._get_calling_module()
        tbl_name = 'kv_' + tbl if tbl is not None else None
        
        if tbl is None or tbl_name not in db:
            if v is not None:
                # module not registered, need to create
                # a new table
                self._register_module(tbl)
                db[tbl_name].insert(k=k, v=repr(v))
            else:
                # no need to delete a non-existent key
                return None
        else:
            if v is not None:
                db[tbl_name].update_or_insert(db[tbl_name].k == k, k=k, v=v)
            else:
                db(db[tbl_name].k == k).delete()
        
        db.commit()
        self._db = db
    
    def __delattr__(self, k):
        self.__setattr__(k, None)
    
    def __getitem__(self, k):
        return self.__getattr__(k)
    
    def __setitem__(self, k, v):
        self.__setattr__(k, v)
    
    def __delitem__(self, k):
        self.__setattr__(k, None)

    def _register_module(self, name):
        db = self._db
        
        tbl_name = 'kv_' + name
            
        if db(db.namespaces.name == name).isempty():
            db.namespaces.insert(name=name)
            db.commit()
        if tbl_name not in db:
            db.define_table(tbl_name,
                            Field('k', 'string', unique=True),
                            Field('v', 'text'),
                            )
        self._db = db

    def _get_calling_module(self):
        # in theory, bot modules will be registered with register_module
        # when they're uploaded and installed

        curfrm = inspect.currentframe()
        for f in inspect.getouterframes(curfrm)[1:]:
            if self.__module__.split('.')[-1] not in f[1]:
                calling_file = f[1]
                break
        caller_mod = inspect.getmodulename(calling_file)
    
        db = self._db
        mod = db(db.namespaces.name == caller_mod)
        if mod.isempty():
            return None
        else:
            return caller_mod
        
    def keys(self):
        db = self._db
        tbl = self._get_calling_module()
        tbl_name = 'kv_' + tbl if tbl is not None else None
        if tbl is None or tbl_name not in db:
            return []
        all_items = db().select(db[tbl_name].ALL)
        all_keys = [r.k for r in all_items]
        return all_keys
    
    def values(self):
        all_keys = self.keys()
        all_vals = list()
        for k in all_keys:
            all_vals.append(self[k])
        return all_vals
    
    def update(self, other):
        for k, v in other.items():
            self[k] = v
        return None
    
    def items(self):
        return zip(self.keys(), self.values())
    
    def iterkeys(self):
        return iter(self.keys())
    
    def itervalues(self):
        return iter(self.values())
    
    def iteritems(self):
        return iter(self.items())
    
    def __iter__(self):
        return iter(self.keys())
    
    def __contains__(self, k):
        if self[k] is not None:
            return True
        else:
            return False
        
    def __copy__(self):
        """Return a dict representing the current table"""
        d = dict()
        d.update(self.items())
        return d
    
    def copy(self):
        """Return a dict representing the current table"""
        return self.__copy__()
    
    def pop(self, k):
        v = self[k]
        self[k] = None
        return v
    
    def popitem(self):
        """Unlike `dict.popitem()`, this is actually random"""
        all_items = self.items()
        removed_item = random.choice(all_items)
        self[removed_item[0]] = None
        return removed_item
    
    def setdefault(self, k, v=None):
        existing_v = self[k]
        if existing_v is None:
            self[k] = v
            return v
        return existing_v
    
    def has_key(self, k):
        return k in self
    
    def get(self, k, v=None):
        existing_v = self[k]
        if existing_v is None:
            return v
        else:
            return existing_v
        
    def clear(self):
        for k in self.keys():
            self[k] = None
