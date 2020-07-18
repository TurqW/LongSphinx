import discord
import re
import utils

noobs = []

async def first_message_link(message, conf):
	automod = conf.get_object(message.guild, 'automod')
	if automod['firstMessage'] and (message.guild.id, message.author.id) in noobs:
		if re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
			await dungeon(', your first message on the server was auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n', message, conf)
		noobs.remove((message.guild.id, message.author.id))

async def no_role_link(message, conf):
	automod = conf.get_object(message.guild, 'automod')
	if 'noRole' in automod and automod['noRole'] and len(message.author.roles) <= 1:
		for blocked in automod['noRole']:
			if blocked in message.content:
				await dungeon(', your message has been auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n', message, conf)

async def dungeon(text, message, conf):
	automod = conf.get_object(message.guild, 'automod')
	role = discord.utils.find(lambda r: r.name.lower() == automod['role'].lower(), message.guild.roles)
	dungeon_channel = utils.find_channel(automod['channel'], message.guild)
	await message.author.add_roles(role)
	await dungeon_channel.send(message.author.mention + text + message.content + '\n```')
	try:
		await message.delete()
		return True
	except Exception as e:
		print(e)

def add_to_noobs(member):
	noobs.append((member.guild.id, member.id))