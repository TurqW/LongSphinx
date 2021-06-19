import logging
import discord

log = logging.getLogger('LongSphinx.AdminModule')

# replace all unused parameters with "**kwargs"
async def ban(
		user, # Author of the message that invoked the command
		channel, # Channel in which command was invoked
		server, # Server in which command was invoked
		mentionTarget, # Used for standard "yourself, unless you tag someone else" systems. If no mentions, return `user`, if 1 return that tagged user, if more than that throw error
		roleMentions,
		command, # Actual command that was passed in. e.g. 'roll' or 'r'
		argstring, # Everything after the first space. Inputs/parameters for the command.
		conf, # Currently active conf object. See botconfig.py
		botname # Name of the active bot, e.g. 'dev' or 'tim'
	):
	if not user.guild_permissions.ban_members:
		return conf.get_string(server, 'cantban')
	id = argstring.strip().strip('<@>!')
	user = discord.Object(id)
	try:
		await server.ban(user)
	except:
		return "Could not ban; either this bot has insufficient permissions or the ID given was invalid."
	return f'Banned user {id}'

# Most of these are probably useless for a readme, but you never know
def readme(
		user, # Author of the message that invoked the command
		channel, # Channel in which command was invoked
		server, # Server in which command was invoked
		mentionTarget, # Used for standard "yourself, unless you tag someone else" systems. If no mentions, return `user`, if 1 return that tagged user, if more than that throw error
		roleMentions,
		command, # Actual command that was passed in. e.g. 'roll' or 'r'
		argstring, # Everything after the first space. Inputs/parameters for the command.
		conf, # Currently active conf object. See botconfig.py
		botname # Name of the active bot, e.g. 'dev' or 'tim'
	):
	return "Ban an account by @mention or ID number. Only takes effect if the user has permissions to ban members from this server; can be used even if the user being banned has already left the server."
