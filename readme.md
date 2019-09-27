# LongSphinx, aka Tim the Diviner

For a list of available commands, hit !readme on a running instance.

# Installation instructions: (WIP)

## Prereqs
1. Tim runs on python 3 (Tested with Python 3.5). The following instructions all assume that running "python" on your machine runs python 3. If this is not the case, replace `python` in these instructions with whatever command will run python 3.
2. Install all dependencies. From the LongSphinx root directory (the one containing 'requirements.txt'), run `python -m pip install -r requirements.txt`.

## Create a bot token
3. Go to https://discordapp.com/developers/applications/. Sign in.
4. Click "Create an application"
5. Give your application a name. To the best of my knowledge, this name does nothing. You can also upload your bot's profile picture on this page.
6. Click "Bot" in the left sidebar.
7. Click "Add Bot".
8. Give you bot a username.
9. Under "Token" click "copy". Keep this window open; you'll need another field later.

## Run your bot
10. Create a token.txt file in the LongSphinx root directory. Paste the token you just copied into it; other than that it should have nothing but a single newline at the end.
11. From the LongSphinx root directory, run `python corebot.py`.

## Add your bot to a server
12. Go back to the web browser you left open. Click "General Information".
13. Find the "Client ID" and copy it.
14. Put the client ID in the appropriate place in the following link, then put it in your address bar and hit enter:  https://discordapp.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot
15. Follow the on-screen prompts.

## Permissions
16. In the discord app, set Tim's permissions as appropriate.
    * Remember that he'll need the "manage roles" permission if you want him to manage any roles.
    * Remember also that his role will need to be higher in the list (literally, further up the list of roles on your server) than any roles you want him to manage.

You should now have a running, non-configured version of LongSphinx running on your server. To see what's available without further configuration, hit him with a `!readme` command in a channel called bot-commands (his default channel).

## Config file structure

The config file is in YAML. YAML is a lot like JSON; it's designed to have less boilerplate, and adds some useful features to avoid data duplication. A full overview of YAML is outside the scope of this documentation; a useful cheat sheet can be found [here](https://learnxinyminutes.com/docs/yaml/).

The first thing you'll want to do is find your server ID; you can right click your server icon in the Discord app and select "Copy ID" from the bottom of the context menu.

Add the following to the end of config.yaml (including indentation):

```
  'your-server-id':
    strings:
      <<: *defaultStrings
    <<: *defaults
```

In YAML, "anchors" can be created with `&` - for instance, `&defaults`. You can then reference these anchors later with `*`, such as the `*defaults` above.

The `<<:` construction is a special key that indicates that whatever follows should be merged into that level of the hierarchy. However, if a key already exists, it doesn't overwrite it; therefore it should always be at the end of the section, so as to allow your server-specific config to overwrite the defaults.

Note that the "defaultStrings" are imported separately from the rest of the defaults; if this were not the case, attempting to overwrite a single string would result in all of the defaults being lost.

The effect of all this is, because LongSphinx loads the "default" server if the server id is not found, nothing. The above block of YAML simply imports the defaults. HOWEVER, it gives you a place to add any of the other configuration you may want.

One last warning: pay attention to the difference between values:

```
defaultChannel: bot-commands

OR

defaultChannel:
  bot-commands
```

lists:

```
channels:
- bot-commands
```

and maps:

```
element:
  Solar:
  Lunar:
  Gaian:
```

In general, you probably just want to make sure your formatting matches that of the existing servers for any given field.

### Fields:

* name: the name of the server. Not actually used; just meant as an aid in navigating the config file.
* channels: a `list` of channels in which the bot should respond to messages.
* greetingChannel: the channel in which the bot should greet new members.
* leavingChannel: the channel in which the bot should announce member departures (leave out to get no such announcements)
* generators: a `list` of generators to have on this server. These map to filenames in the genConfig folder; in general, the default will include all of them that are considered "standalone".
* strings: This contains all of the configurable strings; these are the things that the bot can say.
  * roleChange: What the bot says when someone successfully requests a new role. {0} will tag the person whose role is changed, {1} is the name of the new role.
  * roleClear: What the bot says when a person's roles of a specific roleset have been cleared. {0} will tag the person whose roles were changed, {1} will name the roleset that has been cleared.
  * diceResults: What the bot says when someone rolls dice. {0} tags the person who requested the roll, {1} is the list of all results, and {2} is the total.
  * rerole: What the bot says when someone requests a new random assignment with `!rerole` (only works with `defaultRoleset`). {0} tags the requester, {1} names their new role.
  * invalid<rolesetname>: What the bot says when someone requests a role that's not in that roleset (or doesn't exist). {0} tags the requester, {1} is the role they requested.
  * welcome: What the bot says when someone joins the server. {0} tags them, {1} is the name of their randomly-assigned role (if a `defaultRoleset` is set)
  * left: What the bot says when someone leaves the server. {0} tags them, though obviously they won't receive the tag notification.
  * <rolesetname>RoleList: What the bot says when someone requests the list of roles in a roleset. {0} gives a comma-separated list of the roles, and an image set under `urls: roleImage: <rolesetname>:` will be embedded if available.
* defaultRoleset: This is the name of the roleset that is randomly picked from when someone joins. If left blank, no random role will be assigned.
* rolesets: a `map` of available rolesets. Anatomy of a roleset will be covered later.
* urls: This is a `map`; for now it's only used if you want the list for a roleset to display as an image. This should look like:
```
    urls:
      roleImage:
        rolesetName:
          'http://some.url.here/to/an.image'
```

### Anatomy of a Roleset

A roleset is a `map` of `map`s (of `list`s). At its most basic, it should look like:

```
  rolesets:
    <rolesetname>:
      <rolename1>:
      <rolename2>:
      <rolename3>:
```

<rolesetname> is the name of the roleset; this is used as-is as the command for viewing the list of, requesting, and clearing roles in this roleset, so choose it appropriately. (However, it can be changed later without any loss of data.)

Each <rolename> is the literal name of the role. Behavior is undefined if you have multiple roles on your server with that name. Do not leave off the colon on each line.

Optionally, each role may include a list of `secondaryRoles` which will also be applied when that role is assigned or requested. These will not be cleared on role update or role clear unless they're included in the `removeOnUpdate` list, which should be a sibling to the individual roles.

Note that requesting a role within a roleset will clear any other roles in that roleset (and any in that roleset's `removeOnUpdate` list).

Also, you can optionally include a "description" under each role; the feature to utilize these has not yet been implemented.
