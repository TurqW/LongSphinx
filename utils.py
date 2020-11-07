import os
import discord

fullGaugeChar = '='
emptyGaugeChar = ' '

def check_path(name):
	if not os.path.exists(name):
		os.makedirs(name)

def drawGauge(value, max):
	return '[' + fullGaugeChar*value + emptyGaugeChar*(max-value) + ']'

def find_self_member(client, server):
	return next(member for member in server.members if member.id == client.user.id)

def find_channel(channel_name, server):
	return next(channel for channel in server.channels if channel.name == channel_name or str(channel.id) == str(channel_name))

def getMentionTarget(message):
	if len(message.mentions) < 1:
		return message.author
	elif len(message.mentions) > 1:
		raise ValueError("Too many people tagged")
	else:
		return message.mentions[0]

def is_command(mystring, command):
	mystring = mystring.strip(' !')
	if mystring.split()[0].lower() == command.lower():
		return True
	return False

def embed_to_text(embed):
	text = ''
	if embed.title:
		text += '**' + embed.title + '**\n'
	if embed.description:
		text += embed.description + '\n'
	text += '\n'.join([f'{field.name}: {field.value}\n' for field in embed.fields])
	return text

async def get_pic(user, mentionTarget, server, argstring, **kwargs):
	embed = discord.Embed()
	if 'server' == argstring:
		embed.set_image(url=server.icon_url_as(static_format='png'))
		return {'text': f"{server.name}'s icon!", 'embed':embed }
	embed.set_image(url=mentionTarget.avatar_url_as(static_format='png'))
	return {'text': f"{mentionTarget.mention}'s avatar!", 'embed':embed }

def pic_help():
	return "Shows a bigger version of someone's avatar!"
