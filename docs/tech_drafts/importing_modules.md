This document outlines how Seshet instances will choose, import, and use modules designed to extend the bot's behavior by processing IRC events.

## Module registry

So that the same module can be used by multiple bots with differing configurations, Seshet registers each module in a database table which also contains information such as usage, flood protection controls, authentication and authorization, and channel conditions which may enable or disable a module.

### Registry table: db.modules

Note if manually editing database entries that `pydal` uses the pipe character (`|`) as a separator in lists for most databases (the exception being NoSQL options such as Google datastore which have a native list type). Actual pipe characters in the data are escaped with another pipe (`||`).

* name (string) - The module name which is passed to `importlib.import_module()`.
* enabled (boolean) - Globally enable/disable the module, leaving all other settings intact.
* description (text) - By default, the docstring of the module. Used when the core command `!help` is invoked with no arguments to list all enabled modules and a brief description of their usage or what they do.
* echannels (list:string) - Channels the module is enabled on.
* dchannels (list:string) - Channels the module is explicitly disabled on. Overrides both `echannels` and `enicks`.
* enicks (list:string) - If nick is present in the same channel as the bot, the module is enabled in that channel. Defaults to the bot's own nickname.
* dnicks (list:string) - If nick is present in the same channel as the bot, disables the module. Overrides both `echannels` and `enicks`. Useful if there's another less advanced bot in the channel with similar functionality.
* whitelist (list:string) - List of hostmasks. If the event source is in this list, run the module regardless of the other channel and nick lists.
* blacklist (list:string) - Same as `whitelist`, except never run this module if the event source is in this list. Good for banning abusers.
* cmd_prefix (string, length 1) - Override global command prefix (default: `!`).
* acl (json) - Define an access control list for this module (see below).

### Access control lists: db.modules.acl

Seshet has four authentication options for users: NickServ, username and password, nickname and password, and password only.

With NickServ authentication, all authentication is offloaded to NickServ. A number of NickServ accounts may be specified for authorization, and then authentication can be queried by messaging NickServ `ACC <nickname> *` and parsing the results for an account name. NickServ authentication is recommended for most use cases.

Username and password authentication requires a user to send the bot (in private message) an invocation of the `auth` command with two arguments: username and password. The user will remain authenticated for the duration of their session.

Nickname and password is similar, but `auth` only requires one argument: the password. The bot will take the user's nickname as their username. Like nickname and password, the user will remain authenticated for the duration of their session.

Likewise, password authentication only requires a password as the argument to `auth`, but it can be used from any nickname.

Each module has an access control list stored in the database as json. Upon registering a module, Seshet will usually build a default ACL with an "anyone" role. Certain core modules will have a more complex ACL built by default allowing certain commands to only be used by the owner of the bot (defined in the bot's configuration file or `SeshetBot.owner`). Example:

```json
{
  "owner": {
    "nickserv": "Kopachris",
    "user": "Kopachris"
  },
  "admin": {"group": ["wheel", "admin"]},
  "anyone": {}
}
```

Access control roles are defined by credentials and method of authentication. Each role can use one or more authentication methods, and each authentication method can accept one or more credentials. Valid authentication methods are: `nickserv`, `user`, `password`, and `group`. `group` authentication uses either username and password (if a username is provided) or nickname and password (if a username is not provided) for authentication and then checks the user's group membership for authorization. `user` references a nickname in the `auth_users` table. `password` authentication references an ID in the `auth_pwd` table. `group` authentication references a group name in the `auth_groups` table.

The advantages of this approach are that json is easy to parse (being natively supported by `pydal`) and, if implemented properly, defining roles in terms of authentication methods and accepted credentials will allow admins to easily extend the Seshet's authorization system with new authentication methods.

**Please note that Seshet does not perform any access control on its own. It is still up to the module to restrict access as needed by checking a user's authorization.** Seshet will provide a helper method for checking a user's roles for a given module. Some standard group and role names will be suggested in Seshet's API documentation.

### Registering modules

When a bot is initialized with a new database, it will automatically register and enable the `core` module. This module contains commands essential for administration of the bot. After the bot connects to an IRC network, the owner can automatically register all default modules by invoking the `addmodule` command with a wildcard character, `*`. Alternatively, the owner can register individual modules by giving their names to the `addmodule` command.

## Import mechanics

We have two requirements for importing modules in Seshet:

0. Modules must be dynamic, i.e. changes made to a module must take effect immediately without having to restart the bot
0. Modules must be easy to add, remove, replace, and modify

### Dynamic modules

Modules should be dynamically loaded. That is, they should only be loaded as needed. In order to ensure *all* objects in a module are reloaded (other than the ones stored in `SeshetBot.session` or `SeshetBot.storage`), modules must be unloaded after each use.

It's generally frowned upon to delete modules using the `del` statement. Such deletions are typically incomplete because the way modules are used often means references to objects within the module still exist that the garbage collector can't remove.

So how do we do this cleanly? We can't. We can only do it "well enough." The original BotenAlfred accomplishes this by `del`eting a module when finished with it and `reload()`ing it immediately after the next import.

*If someone has a better idea, feel free to open an issue for it.*

### Global modules and user modules

The default modules included with Seshet will normally be installed as a package, `seshet_modules` in the Python installation's site-packages directory. However, to make modules as easy as possible to work with, the bot should also check for, and prefer, a user-specified directory for modules.

This will be done by importing `seshet_modules` at the top level of `bot` and including some code in `run()`:

```python
if self.module_directory is not None:
    seshet_modules.__path__.insert(0, self.module_directory)
```

When the module is imported from the `seshet_modules` package, then, the Python interpreter will first look in the directory specified by `self.module_directory`, and then the package directory itself.
