import discord
import re
import utils

noobs = []

async def first_message_link(message, conf, client):
	automod = conf.get_object(message.server, 'automod')
	if automod['firstMessage'] and (message.server.id, message.author.id) in noobs:
		if re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
			await dungeon(', your first message on the server was auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n', message, conf, client)
		noobs.remove((message.server.id, message.author.id))

async def no_role_link(message, conf, client):
	automod = conf.get_object(message.server, 'automod')
	if 'noRole' in automod and automod['noRole'] and len(message.author.roles) <= 1:
		for blocked in automod['noRole']:
			if blocked in message.content:
				await dungeon(', your message has been auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n', message, conf, client)

async def dungeon(text, message, conf, client):
	automod = conf.get_object(message.server, 'automod')
	role = discord.utils.find(lambda r: r.name.lower() == automod['role'].lower(), message.server.roles)
	dungeon_channel = utils.find_channel(automod['channel'], message.server)
	await client.add_roles(message.author, role)
	await client.send_message(dungeon_channel, message.author.mention + text + message.content + '\n```')
	try:
		await client.delete_message(message)
		return True
	except Exception as e:
		print(e)

def add_to_noobs(member):
	noobs.append((member.server.id, member.id))