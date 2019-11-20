import discord

noobs = []

async def first_message_link(message, conf):
	automod = conf.get_object(message.server, 'automod')
	if automod and (message.server.id, message.author.id) in noobs:
		if re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
			role = discord.utils.find(lambda r: r.name.lower() == automod['role'].lower(), message.server.roles)
			dungeon_channel = find_channel(automod['channel'], message.server)
			await client.add_roles(message.author, role)
			await client.send_message(dungeon_channel, message.author.mention + ', your first message on the server was auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n' + message.content + '\n```')
			try:
				await client.delete_message(message)
				return True
			except Exception as e:
				print(e)
		noobs.remove((message.server.id, message.author.id))