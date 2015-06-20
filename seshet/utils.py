"""Various utility classes used by the bot and command modules.

`Storage` is copied from gluon.storage, part of the web2py framework,
    Copyrighted by Massimo Di Pierro <mdipierro@cs.depaul.edu>,
    License: LGPLv3 (http://www.gnu.org/licenses/lgpl.html)
"""

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
        bar
        
    Or like a dict:
    
        >>> store[spam] = 'eggs'
        >>> store[spam]
        eggs
        
    The KVStore object uses `inspect` to determine which module
    the object is being accessed from and will automatically create
    a database table as needed or determine which one to use if it
    already exists.
    """

    def __init__(self, db):
        global _db_store
        
        # store name of app these settings were set up in used later
        # for defining safe directories in _get_calling_module()
        #
        # the file which starts the bot daemon will have to create a 
        # new instance of Settings after injecting current.request.application
        # into the module object: import bot_utils; bot_utils.current = Storage()
        # etc.
        self.__dict__['_app'] = current.request.application
        
        # define some tables
        
        if 'bot' not in db:
            # general bot-wide settings
            db.define_table('bot',
                            Field('k', 'string', unique=True),
                            Field('v', 'text'),
                            Field('is_str', 'boolean'),
                            )
        if 'modules' not in db:
            # list of registered modules and their unique table names
            db.define_table('modules',
                            Field('name', 'string'),
                            Field('uuid', 'string'),
                            )
        for m in db().select(db.modules.ALL):
            # these are modules' own "namespaces"
            if m.uuid != m.name:
                db.define_table(m.uuid,
                                Field('k', 'string', unique=True),
                                Field('v', 'text'),
                                Field('is_str', 'boolean'),
                                )
        _db_store.db = db   # web2py DAL instance

    def __getattr__(self, k):
        global _db_store
        
        # get DAL object (db) and table name (tbl)
        tbl = self._get_calling_module()
        if tbl is None:
            # module not registered, not in safe dirs
            # deny access
            return None
        if (k == '_Settings__db' or k == '__db') and tbl == 'bot':
            return _db_store.db
        
        db = _db_store.db
        if tbl not in db:
            # module hasn't tried to store anything,
            # table doesn't exist
            return None
        
        r = db(db[tbl].k == k)
        if r.isempty():
            # key has not been set, follow behavior
            # established by gluon.storage.Storage
            # and return None
            return None
        
        r = r.select().first()
        if r.is_str:
            # string literal, don't eval() because
            # it won't have quotes
            return r.v
        else:
            # other literal, eval() will return
            # the proper type of object
            return eval(r.v)

    def __setattr__(self, k, v):
        global _db_store
        
        tbl = self._get_calling_module()
        if tbl is None:
            # module not registered, not in safe dirs
            # deny access
            return None
        db = _db_store.db
        if (k == '_Settings__db' or k == '__db') and tbl == 'bot':
            _db_store.db = v
            return

        # __getattr__ will normally eval() whatever's stored in
        # the database entry so it can get int, list, etc. literals
        # but we don't want to require quote marks for strings
        #
        # e.g.
        # an int will be stored as 3
        # a float will be stored as 3.14
        # a list will be stored as [0, 1, 1, 2, 3, 5, 8]
        # a tuple will be stored as ('spam and eggs', 'spam beans bacon and spam')
        # a dict will be stored as {'1fish': 'red', '2fish': 'blue'}
        # a string will be stored as foo bar baz bang spam eggs (without quotes)
        
        is_str = isinstance(v, str) or isinstance(v, unicode)
        
        if tbl in db:
            if v is not None:
                db[tbl].update_or_insert(db[tbl].k == k,
                                         k=k, v=v, is_str=is_str)
            else:
                db(db[tbl].k == k).delete()
        elif v is not None:
            # storage hasn't been allocated yet, need to register
            # the module and receive a uuid
            tbl = self.register_module(tbl, True)
            db[tbl].insert(k=k, v=v, is_str=is_str)
        else:
            return None
        _db_store.db = db
    
    def __delattr__(self, k):
        self.__setattr__(k, None)
    
    def __getitem__(self, k):
        return self.__getattr__(k)
    
    def __setitem__(self, k, v):
        self.__setattr__(k, v)
    
    def __delitem__(self, k):
        self.__setattr__(k, None)

    def register_module(self, name, create_table=False):
        global _db_store
        if name in ('modules', 'bot'):
            # name collision with existing tables
            raise ValueError('The module name %s is reserved' % name)
        db = _db_store.db
        if create_table:
           # only create a table if something will actually be stored
           # usually called from self.__setattr__()
           mod_uuid = name + uuid.uuid4().hex
           # using uuid to obscure names a little
           db.define_table(mod_uuid,
                           Field('k', 'string', unique=True),
                           Field('v', 'text'),
                           Field('is_str', 'boolean'),
                           )
        else:
           # not making table, use module's name as placeholder
           # in __setattr__(), if module's name == its "uuid",
           # call this function again with create_table=True
           mod_uuid = name
        #mod_uuid = name
        db.modules.update_or_insert(db.modules.name == name, name=name, uuid=mod_uuid)
        _db_store.db = db
        return mod_uuid

    def _get_calling_module(self):
        global _db_store
        
        # in theory, bot modules will be registered with register_module
        # when they're uploaded and installed
        # all other "modules" that can use this object will be models
        # and controllers
        # since they won't be registered, they'll use the table 'bot'

        curfrm = inspect.currentframe()
        for f in inspect.getouterframes(curfrm)[1:]:
            if self.__module__.split('.')[-1] not in f[1]:
                calling_file = f[1]
                break
        caller_mod = inspect.getmodulename(calling_file)
        #log = open('bot_access.log', 'a')
        #log.write('%s:%s\n' % (self.__module__, caller_mod))
        #log.close()
    
        db = _db_store.db
        try:
            mod = db(db.modules.name == caller_mod)
        except AttributeError:
            # db doesn't exist yet, still in setup phase
            #_db_store.db = list()
            return 'bot'
        if mod.isempty():
            # calling module not registered, probably bot itself or
            # web interface's models/controllers
            # can verify better by initializing Settings with current.request
            #return None
            curapp = self._app
            # safe_dirs = (['applications', curapp, 'controllers'],
            #              ['applications', curapp, 'models'],
            #              ['applications', curapp, 'private'],
            #              )
            safe_suf = ('controllers',
                        'models',
                        'private',
                        'modules/bot_utils',
                        'modules/prefs',
                        )
            safe_dirs = ['applications/' + curapp + '/' + d for d in safe_suf]
            self.__dict__['_debug_calling_file'] = calling_file
            #calling_file = calling_file.split('/')
            safe = False
            for d in safe_dirs:
                if d in calling_file:
                    safe = True
                    break
                
            if safe:
                return 'bot'
            else:
                # calling module not in safe directories, deny access
                return None
        else:
            return mod.select().first().uuid
        
    def test(self):
        curfrm = inspect.currentframe()
        for f in inspect.getouterframes(curfrm)[1:]:
            if self.__module__ not in f[1]:
                calling_file = f[1]
                break
        caller_mod = inspect.getmodulename(calling_file)
        curapp = self._app
        db = _db_store.db
        mod = db(db.modules.name == caller_mod).select().first()
        empty = db(db.modules.name == caller_mod).isempty()
        return locals()
        
    def keys(self):
        db = _db_store.db
        tbl = self._get_calling_module()
        if tbl is None or tbl not in db:
            return []
        all_items = db().select(db[tbl].ALL)
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
        """Unlike dict.popitem(), this is actually random"""
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