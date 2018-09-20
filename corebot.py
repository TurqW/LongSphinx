# GENERAL TODOs WITHOUT A PLACE TO LIVE:
# - start on boot? (https://www.raspberrypi.org/forums/viewtopic.php?t=66206#p485866 ?)
# - write uncaught exceptions to log (instead of stderr)
# - change conf through chat?
#    - add/remove roles
# - fortune?
# - !help

import discord
import random
import yaml
import logging
logging.basicConfig(filename='ubeast.log',level=logging.DEBUG)

log = logging.getLogger('LongSphinx')

import namegen
import wandgen
import companiongen
import botconfig as conf
import botdice as dice

with open('token.txt', 'r') as tokenfile:
	TOKEN = tokenfile.readline()[:-1]

client = discord.Client()
todo = []

@client.event
async def on_message(message):
	for member, role in todo:
		try:
			await add_role(member, role)
		except discord.errors.NotFound:
			# If they've already left, we wantto know, but to remove it from todo
			log.info('Member {0.name} not found on server {0.server}'.format(member))
	todo.clear()
	# we do not want the bot to reply to itself
	conf.update_config()
	if message.author == client.user:
		return

	# TODO: more robust plugin/command parser module?
	if message.channel.name in conf.get_object(message.server.id, 'channels'):
		if message.content.startswith('!name'):
			# Generate random fantasy name
			await gen_name(message)

		if message.content.startswith('!role'):
			# Role requests
			await request_role(message)

		if message.content.startswith('!list'):
			await list_roles(message)

		if message.content.startswith('!roll'):
			#dice
			await roll_dice(message)

		if message.content.startswith('!rerole'):
			await rerole(message)

		if message.content.startswith('!wand'):
			await gen_wand(message)

		if message.content.startswith('!summon'):
			await gen_companion(message)

@client.event
async def on_ready():
	log.debug('Bot logged in as {0.user.name}'.format(client))
	print('Bot started')

@client.event
async def on_member_join(member):
	channel = find_channel(conf.get_object(member.server.id, 'greetingChannel'), member.server)
	log.debug('{0.name} joined {0.server}'.format(member))
	role = random.choice(get_valid_role_set(member.server))
	await change_role(member, role.name)
	msg = conf.get_string(member.server.id, 'welcome').format(member.server, member, role, find_channel(conf.get_object(member.server.id, 'greetingChannel'), member.server))
	await client.send_message(channel, msg)

async def gen_name(message):
	msg = 'Your generated name: {0}'.format(namegen.generate_name())
	await client.send_message(message.channel, msg)

async def gen_wand(message):
	msg = wandgen.generate_wand()
	await client.send_message(message.channel, msg)

async def gen_companion(message):
	msg = companiongen.generate_companion()
	await client.send_message(message.channel, msg)

async def request_role(message):
	words = message.content.split()
	words.pop(0)
	try:
		newRole = await change_role(message.author, ' '.join(words))
		#todo "an elf" etc
		msg = conf.get_string(message.server.id, 'roleChange').format(message, newRole.name)
	except (NameError):
		msg = conf.get_string(message.server.id, 'invalidRole').format(message, ' '.join(words))
	await client.send_message(message.channel, msg)

async def list_roles(message):
	roles = [x.name for x in get_valid_role_set(message.server)]
	roles.sort()
	msg = conf.get_string(message.server.id, 'roleList').format(', '.join(roles))
	imgurl = conf.get_object(message.server.id, 'urls', 'roleImage')
	if imgurl:
		embed = discord.Embed().set_image(url=imgurl)
	await client.send_message(message.channel, msg, embed=embed)

async def roll_dice(message):
	toRoll = message.content.split()
	toRoll.pop(0)
	results = dice.roll_command(toRoll)
	resultString = ', '.join([str(i) for i in results])
	msg = conf.get_string(message.server.id, 'diceResults').format(message, resultString, sum(results))
	await client.send_message(message.channel, msg)

async def rerole(message):
	role = await random_role(message.author)
	msg = conf.get_string(message.server.id, 'rerole').format(message, role)
	await client.send_message(message.channel, msg)

async def random_role(member):
	role = random.choice(get_valid_role_set(member.server))
	await change_role(member, role.name)
	return role

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
