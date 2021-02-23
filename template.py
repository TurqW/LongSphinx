
# replace all unused parameters with "**kwargs"
async def direct_command(
		user, # Author of the message that invoked the command
		channel, # Channel in which command was invoked
		server, # Server in which command was invoked
		mentionTarget, # Used for standard "yourself, unless you tag someone else" systems. If no mentions, return `user`, if 1 return that tagged user, if more than that throw error
		command, # Actual command that was passed in. e.g. 'roll' or 'r'
		argstring, # Everything after the first space. Inputs/parameters for the command.
		conf, # Currently active conf object. See botconfig.py
		botname # Name of the active bot, e.g. 'dev' or 'tim'
	):
	return "You can return text to reply as a message, or a dict with several useful fields (example TK)"

# Most of these are probably useless for a readme, but you never know
async def readme(
		user, # Author of the message that invoked the command
		channel, # Channel in which command was invoked
		server, # Server in which command was invoked
		mentionTarget, # Used for standard "yourself, unless you tag someone else" systems. If no mentions, return `user`, if 1 return that tagged user, if more than that throw error
		command, # Actual command that was passed in. e.g. 'roll' or 'r'
		argstring, # Everything after the first space. Inputs/parameters for the command.
		conf, # Currently active conf object. See botconfig.py
		botname # Name of the active bot, e.g. 'dev' or 'tim'
	):
	return "Return a useful help message. Has all the same return possibilities as a direct command."

async def reactListener(
		reaction, # discord 'reaction' object
		client # discord client
	)