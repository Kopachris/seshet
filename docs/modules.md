**Note: This document is an old proposal and is subject to change.**

Seshet is highly extensible through the use of modules.  Modules are written in Python 3.4, same as Seshet, and contain various global variables (which are stored in the database when the module is installed, and can be changed afterward) which tell Seshet whether or not to run the module for a given IRC event.  These variables are:

* **event_type** - List of one or more of `'PRIVMSG'`, `'QUIT'`, `'JOIN'`, `'PART'`, `'KICK'`, or `'CTCP_ACTION'`.  Event types for which the module will be run. _default:_ `['PRIVMSG']`
* **description** - Detailed description of what the module does.  Will be listed in the bot's built-in 'help' command if there are no commands registered to this module.
* **cmd_char** - Override the global command prefix (_default:_ `'!'`).  Each registered command (below) must begin with this in chat.  The purpose of being able to override the command prefix on a per-module basis would be to allow commands whose names overlap with another bot's commands (or the same bot's commands), but whose functions differ.
* **commands** - Dictionary of commands recognized by this module and their descriptions **not** including the command prefix, e.g. `{'foo': 'Does foo', 'bar': 'Does bar'}`.  The command prefix will automatically be checked by the bot when determining which modules to run for a given event.  If there are no commands registered by a module, the module is assumed to do its own event checking (e.g. a module which uses regex to reply to a more complex general statement, rather than a specific command) and will always run as long as it meets other requirements.  The commands (with prefix added automatically) and their descriptions will be listed in the bot's built-in 'help' command.

# Installing modules
_TO DO: Update this_

Modules can be installed by uploading a .py file to the bot using the module upload page (default: `http://localhost/botenalfred/admin/upload`).  Modules can also be uploaded to the `web2py/applications/botenalfred/modules` directory using any other method (e.g. SFTP) and then can be installed by entering the module's filename (without the .py extension) on the same module upload page.  In a future version, the module upload page will also be able to retrieve a module from a URL.

Because modules are loaded at run time, modules can be installed and can have their settings changed while the bot is running.  Modules are re-imported for every event.

After uploading, the bot will import the module, create a database entry for it, and run its `init()` method.  You will then be redirected to the module's settings page, where you will be able to edit its settings.  Every module has the following settings:

## Module settings

* **Enabled?** - Whether or not the module is globally enabled.  If this box is not checked, the module will never be run.  If it is checked, it will be run according to the module's other settings.
* **Event type** - _(list)_ Type of IRC event(s) this module handles.  List of one or more of `'PRIVMSG'`, `'QUIT'`, `'JOIN'`, `'PART'`, `'KICK'`, or `'CTCP_ACTION'`.  The module will only be run for events of these types.  If a module is capable of handling more than one type of event, the module will still be responsible for differentiating between event types.  You'll usually want to leave this setting to whatever the module was initialized with, but it may be useful to change if, for example, you have a module which defaults to handling both PRIVMSG and CTCP_ACTION events, but you'd rather it only handled PRIVMSG events.
* **Name** - Self-explanatory.  Defaults to the filename of the uploaded module.  Shouldn't change.
* **Description** - Long description of what the module does.  Given to users using the `!help module <name>` command.
* **Channels enabled** - _(list)_ Channels for which this module will be run, unless a user listed in **Nicks disabled** is present in the channel.  Default is blank.
* **Channels disabled** - _(list)_ Channels for which this module is not run, overriding **Nicks enabled**.  Default is blank.
* **Nicks enabled** - _(list)_ When users in this list are present in a channel, the module will be run on that channel unless that channel is listed in **Channels disabled**.  Default is blank, but in most cases you'll want to add the bot's nickname here so that the module is enabled on every channel the bot is present in.
* **Nicks disabled** - _(list)_ When users in this list are present in a channel, the module will not be run on that channel.  Default is blank.
* **Command prefix** - Used to override the global command prefix (default: '!') in case of conflicting commands.
* **Requires authentication?** - Whether or not the module requires authentication for users to use it.  Defaults to false (not checked).
* **Authentication mode** - Whether to use web2py, NickServ, plain password, or challenge-response for authentication.  See _Authentication modes_ below for more details.

### Determining whether to run a module

Seshet is fairly intelligent about determining which modules to run.  For a given event, the bot first retrieves a list of globally-enabled modules associated with that event type.  Next, the bot tries to determine whether the event was targeted at the bot itself.  If the event has the bot's nickname as `event.target` (such as a private message directed toward the bot), then the event was obviously targeted.  Otherwise, the bot checks if the bot's nickname, username, or real name is present in `event.message` (not cap-sensitive).  If so, the bot considers the event targeted.  If `event.message` actually begins with the bot's nick, user, or real name, the bot removes it from `event.message` before proceeding.

If the event is not targeted, Seshet narrows the list of modules down to those which fulfill **Channels enabled** or **Nicks enabled** for this event and which aren't disabled by **Channels disabled** or **Nicks disabled** for this event.  If the event _is_ targeted, Seshet leaves the list as-is.

Next, Seshet checks the first word of `event.message` and determines if any registered commands match.  If a registered command matches and its associated module is in the list of enabled modules for this event, Seshet runs that module first using the function associated with that command instead of `run()`.

Afterward, Seshet calls the `run()` method of each module in the list (including the one which matched a command).

_Implementation note: "Narrowing the list" will probably be done by using different SQL queries for targeted and untargeted events.  A separate SQL query will be used for checking commands._

### Authentication modes

* _web2py_ - web2py (the web framework the bot is based on) includes its own authentication system.  The bot administrator will have to set up an account for each user with an email address and password.  Users will have to authenticate with the bot by sending it the command `!auth <email> <password>`.  Users will remain authenticated as long as they are present in a channel the bot is also present in as long as the bot is running.  If this authentication mode is selected, another field, **Restrict to group** _(list)_ will be available which will allow the module to be restricted to users who are members of one or more groups.

* _NickServ_ - The bot will send `ACC <user> *` to NickServ to determine what account a user is logged in to.  If this authentication mode is selected, another field, **Restrict to user** _(list)_ will be available which will allow the module to be restricted to one or more NickServ accounts.

* _Plain password_ - The user must authenticate with the bot by sending the command `!auth <password>`.  The user will remain authenticated for modules with the same password as long as they are present in a channel the bot is also present in as long as the bot is running.  Any user who gives the correct password will be accepted.  If this authentication mode is selected, another field, **Password** will be available which will allow you to set the password.

* _Challenge-response_ - Only added for fun.  Classic sign-countersign style authentication.  When a user tries to use the module for the first time, the bot will challenge them in a private message.  If the user provides an appropriate countersign, the module will run and they will remain authenticated for modules with the same challenge as long as they are present in a channel the bot is also present in as long as the bot is running.  Any user who gives the correct countersign will be accepted.  If this authentication mode is selected, three more fields, **Challenge**, **Response**, and **Number of keys for authentication** will be available to set the challenge and response.

    The **Response** field is a list of keywords, and a user's response must include at minimum **Number of keys for authentication** keywords in order for authentication to be accepted.  For example, if the challenge is "How was the drive from Istanbul?" the module might be set up to accept two or more of the keywords "drive," "magical," or "Tahiti."  The responses "The **drive** was **magical**," "The **drive** was to **Tahiti**," or "**Tahiti** is a **magical** place" would all be accepted.

# Writing modules

Modules for Seshet are fairly easy to write.  At its simplest, a Seshet module is just:

    description = "foo - does foo"

    def run(bot, event):
        pass

The module must have a description (even if it's blank) and must have either a `run()` method or a `commands` dictionary and corresponding handlers (described below) that accept two parameters: `bot`, and `event`, which are (in order) the bot's instance and the event currently being handled.  The `run()` method is meant primarily for operations which require more detailed parsing than Seshet provides on its own.

Commands can be added like this:

    description = "foo - does foo"
    commands = {'foo': do_foo}

    def do_foo(bot, event):
        """Will reply 'Foo!'"""
        bot.bot_reply(event, "Foo!")

The `commands` dictionary uses the command name for its keys and a function for its values.  If the command prefix is set to `!`, then usage for this example would be:

    <luser> !foo
    <Seshet> luser: Foo!

The docstring in the `do_foo()` method is required (even if blank) and will be used for the help text for that command (returned in private message).  For example:

    <luser> !help
    <Seshet> Installed modules: foo
    <Seshet> -
    <Seshet> Enabled commands:
    <Seshet> !auth - Authenticate with Seshet.
    <Seshet> !help - Display this help. Use '!help <module>' for more details about an installed module.
    <Seshet> !foo - Will reply 'Foo!'

## Special methods

There are five special methods other than `run()` which are used by the bot for non-command purposes.  These methods are `handle_install()`, `handle_uninstall()`, `handle_startup()`, `handle_enable()`, and `handle_disable()`.  Each of these handlers take two parameters: _db_, and _settings_.  _db_ is the web2py DAL instance to provide access to the bot's database, and _settings_ is the module's own persistent key/value store (stored in the same database using a random UUID linked to each module for table names).

* **handle_install**_(db, settings)_ - Runs when the module is uploaded/registered.  May be used to initialize module settings such as reply formats, API keys, etc.
* **handle_uninstall**_(db, settings)_ - Runs when the module is deleted/unregistered from the database.  The `settings` store for this module will automatically be removed and does not need to be removed manually, though any additional database tables may need to be dropped.
* **handle_startup**_(db, settings)_ - Runs every time the bot is started.  May be used to define additional database tables used by the bot.
* **handle_enable**_(db, settings)_ - Runs every time the module is enabled globally from the module's settings page.  May be used to initialize settings that should be persistent for the duration the module is enabled, but should be reset when the module is disabled (game saves or scheduled/recurring tasks, perhaps?).
* **handle_disable**_(db, settings)_ - Converse of `handle_enable()`.  Runs every time the module is disabled globally from the module's settings page.  May be used to reset settings that shouldn't be completely persistent.

`handle_install()` should in most cases also perform the same tasks as or call `handle_enable()` and `handle_startup()`.  Likewise, `handle_enable()` should usually do the same with `handle_startup()` and `handle_uninstall()` should usually do the same with `handle_disable()`.

## Using authentication

Once authentication is set up in the module settings, using authentication in your module is exceedingly simple.  If the authentication mode is "web2py" or "NickServ," then the value of `event.auth` will be the account the user is logged in to, or `False` if not logged in.  If the authentication mode is "Plain password" or "Challenge-response," the value of `event.auth` will be the same as `event.source` if authorized or `False` if not authorized.  If the module is not set up to use authentication, the value of `event.auth` will always be the same as `event.source`.

The actual authentication process is handled automatically by Seshet.  If the authentication mode is "web2py" and the user is not logged in, the user will be prompted to log in using the `!auth` command.  The same applies to "Plain password" and "Challenge-response" authentication modes, except the user will be challenged for a password.

    description = "Authentication example"
    commands = {'foo': do_foo}

    def do_foo(bot, event):
        """Does foo with authentication."""
        bot.bot_reply(event, "Authenticated as %s" % event.auth)

With web2py authentication:

    <luser> !foo
    <Seshet> Please log in with '!auth <email> <password>'
    <luser> !auth luser@example.com mypassword
    <Seshet> Authenticated as luser@example.com

With NickServ authentication:

    <luser> !foo
    <Seshet> Please log in with NickServ and try again
    <luser> /msg NickServ identify mypassword
    <luser> !foo
    <Seshet> Authenticated as luser

With plain password authentication:

    <luser> !foo
    <Seshet> Password?
    <luser> wrongpassword
    <Seshet> Incorrect password for previous command
    <luser> mypassword
    <Seshet> Authenticated as True

With challenge-response authentication:

    <luser> !foo
    <Seshet> How was the drive from Istanbul?
    <luser> the drive from istanbul was magical
    <Seshet> Authenticated as True

For every user, Seshet will remember the last module/command which the user tried to use but didn't have authentication for.  NickServ authentication will require the user to repeat the command after logging in, but web2py, plain password, and challenge-response authentication, which are all performed by interacting with Seshet, will run the module/command upon successful authentication.  Plain password and challenge-response authentication require a module/command which requires authentication to be used before authentication will be attempted, but users can log in for modules/commands which use web2py authentication using the `!auth` command any time.
    
Seshet will still run the `run()` method of modules for which a user is not authenticated, if present.  If `run()` returns `True`, Seshet will not send the message asking the user to log in.  If the method returns `False` or `None`, or the `run()` method isn't present, it will send the message asking the user to log in.  This may be used for modules which prefer to have a custom message asking users to log in.  For example, a mailbox module which tells users how many messages they have before asking them to log in:

    ...

    commands = {'mail': send_mail,
                'inbox': check_mail}

    ...

    def run(bot, event):  # run on both JOIN and PRIVMSG
        # get number of messages for event.source
        if has_msgs and not event.auth:
            bot.send_message(event, "There are %i messages for you.  Please log in and then use the !inbox command to check them." % has_msgs)
            return True
