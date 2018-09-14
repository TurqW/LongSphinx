# GENERAL TODOs WITHOUT A PLACE TO LIVE:
# - load all strings from conf
# - start on boot?
# - write uncaught exceptions to log (instead of stderr)
# - change conf through chat?

import discord
import random
import yaml
import logging
logging.basicConfig(filename='ubeast.log',level=logging.DEBUG)

log = logging.getLogger('CoreBot')

import namegen
import botconfig as conf

with open('token.txt', 'r') as tokenfile:
	TOKEN = tokenfile.readline()[:-1]

client = discord.Client()
todo = []

@client.event
async def on_message(message):
	for member, role in todo:
		await add_role(member, role)
	todo.clear()
	# we do not want the bot to reply to itself
	conf.update_config()
	if message.author == client.user:
		return

	if message.channel.name in conf.get_object(message.server.id, 'channel'):
		if message.content.startswith('!hello'):
			# Hello debug message, just to make sure the bot is on
			msg = 'Hello {0.author.mention}'.format(message)
			await client.send_message(message.channel, msg)

		if message.content.startswith('!name'):
			# Generate random fantasy name
			msg = 'Your generated name: {0}'.format(namegen.generate_name())
			await client.send_message(message.channel, msg)

		if message.content.startswith('!role'):
			# Role requests
			words = message.content.split()
			words.pop(0)
			try:
				newRole = await change_role(message.author, ' '.join(words))
				#todo "an elf" etc
				msg = '{0.author.mention}, you are now a {1}'.format(message, newRole.name)
			except (NameError):
				msg = '{0.author.mention}, role {1} is not on the valid list.'.format(message, ' '.join(words))
			await client.send_message(message.channel, msg)

		if message.content.startswith('&join'):
			# Randomize role for member, as though they just joined (for debug purposes)
			await on_member_join(message.author)
		
@client.event
async def on_ready():
	log.debug('Bot logged in as {0.user.name}'.format(client))
	print('Bot started')

@client.event
async def on_member_join(member):
	channel = find_channel(conf.get_object(member.server.id, 'greetingChannel'), member.server)
	role = random.choice(get_valid_role_set(member.server))
	log.debug('{0.mention} joined {0.server} and has been assigned role {1.name}'.format(member, role))
	await change_role(member, role.name)
	msg = '''Welcome to {0.name}, {1.mention}. You seem to be a ... {2.name}, perhaps?
My crystal ball has been foggy of late. If I\'m wrong, quest to the pinned message in {3.mention} to change your character, adventurer!'''.format(member.server, member, role, find_channel(conf.get_object(member.server.id, 'channel'), member.server))
	await client.send_message(channel, msg)


async def add_role(member, role):
	log.debug('adding {0.name} to {1.name} on {2.name}'.format(role, member, member.server))
	roles = [role]
	if role.name in conf.get_object(member.server.id, 'validRoles').keys():
		for roleName in conf.get_object(member.server.id, 'validRoles', role.name, 'secondaryRoles'):
			secondRole = discord.utils.find(lambda r: r.name.lower() == roleName.lower(),   member.server.roles)
			if secondRole not in member.roles:
				roles = roles + [secondRole]
	await client.add_roles(member, *roles)

def find_channel(channel_name, server):
	for x in server.channels:
		if x.name == channel_name:
			return x
	log.error('channel {0} not found on server {1.name}'.format(channel_name, server))

async def change_role(member, roleName):
	if any(role.name.lower() == roleName.lower() for role in get_valid_role_set(member.server)):
		role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.server.roles)
		await client.remove_roles(member, *get_roles_to_remove(member.server))
		todo.append((member, role))
		return role
	else:
		raise NameError(roleName)

def get_valid_role_set(server):
	roleNames = conf.get_object(server.id, 'validRoles').keys()
	validRoles = [x for x in server.roles if x.name in roleNames]
	return validRoles

def get_roles_to_remove(server):
	return get_valid_role_set(server) + [x for x in server.roles if x.name in conf.get_object(server.id, 'removeOnUpdate')]

client.run(TOKEN)
