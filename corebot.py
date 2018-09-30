import discord
import random
import yaml
import sys
import logging

import generator
import botconfig as conf
import botdice as dice

logging.basicConfig(filename='logs/ubeast.log',level=logging.DEBUG)

log = logging.getLogger('LongSphinx')

tokenfilename = 'token.txt'

if len(sys.argv) > 1:
	tokenfilename = sys.argv[1]
	
with open(tokenfilename, 'r') as tokenfile:
	TOKEN = tokenfile.readline()[:-1]

client = discord.Client()
todo = []

@client.event
async def on_message(message):
	for member, roleinfo in todo:
		try:
			await add_role(member, roleinfo[0], roleinfo[1])
		except discord.errors.NotFound:
			# If they've already left, we want to know, but to remove it from todo
			log.info('Member {0.name} not found on server {0.server}'.format(member))
	todo.clear()
	# we do not want the bot to reply to itself
	conf.update_config()
	if message.author == client.user:
		return

	if message.channel.name in conf.get_object(message.server.id, 'channels'):
		if message.content.startswith('!list'):
			# TODO lists for each roleset
			await list_roles(message)

		elif message.content.startswith('!roll'):
			#dice
			await roll_dice(message)

		elif message.content.startswith('!rerole'):
			await rerole(message)

		elif message.content.startswith('!readme'):
			await give_help(message)

		elif message.content.startswith('&join'):
			await on_member_join(message.author)
		
		elif message.content.startswith('!'):
			await parse(message)

@client.event
async def on_ready():
	log.debug('Bot logged in as {0.user.name}'.format(client))
	print('Bot started')

@client.event
async def on_member_join(member):
	channel = find_channel(conf.get_object(member.server.id, 'greetingChannel'), member.server)
	log.debug('{0.name} joined {0.server}'.format(member))
	role = await random_role(member, conf.get_object(member.server.id, 'defaultRoleset'))
	msg = conf.get_string(member.server.id, 'welcome').format(member.server, member, role, find_channel(conf.get_object(member.server.id, 'defaultChannel'), member.server))
	await client.send_message(channel, msg)

async def parse(message):
	command = message.content.split(' ')[0][1:]
	if command in conf.get_object(message.server.id, 'rolesets').keys():
		await request_role(message)
	elif command in conf.get_object(message.server.id, 'generators'):
		msg = generator.generate(command)
		await client.send_message(message.channel, msg)

async def request_role(message):
	words = message.content.split()
	roleset = words.pop(0)[1:]
	if words[0].lower() == 'none' and roleset != conf.get_object(message.server.id, 'defaultRoleset'):
		await client.remove_roles(message.author, *get_roles_to_remove(message.author.server, roleset))
		msg = conf.get_string(message.server.id, 'roleClear').format(message, roleset)
	else:
		try:
			newRole = await change_role(message.author, ' '.join(words), roleset)
			msg = conf.get_string(message.server.id, 'roleChange').format(message, newRole.name)
		except (NameError):
			msg = conf.get_string(message.server.id, 'invalidRole').format(message, ' '.join(words))
	await client.send_message(message.channel, msg)

async def list_roles(message):
	try:
		roleset = message.content.split(' ')[1]
	except (IndexError):
		roleset = None
	if not roleset:
		roleset = conf.get_object(message.server.id, 'defaultRoleset')
	roles = [x.name for x in get_roleset(message.server, roleset)]
	roles.sort()
	msg = conf.get_string(message.server.id, roleset + 'RoleList').format(', '.join(roles))
	imgurl = None
	if roleset in conf.get_object(message.server.id, 'urls', 'roleImage'):
		imgurl = conf.get_object(message.server.id, 'urls', 'roleImage', roleset)
	if imgurl:
		embed = discord.Embed().set_image(url=imgurl)
		await client.send_message(message.channel, msg, embed=embed)
	else:
		await client.send_message(message.channel, msg)

async def roll_dice(message):
	toRoll = message.content.split()
	toRoll.pop(0)
	results = dice.roll_command(toRoll)
	resultString = ', '.join([str(i) for i in results])
	msg = conf.get_string(message.server.id, 'diceResults').format(message, resultString, sum(results))
	await client.send_message(message.channel, msg)

async def rerole(message):
	role = await random_role(message.author, conf.get_object(message.server.id, 'defaultRoleset'))
	msg = conf.get_string(message.server.id, 'rerole').format(message, role)
	await client.send_message(message.channel, msg)

async def give_help(message):
	msg = 'Role operations:\n'
	msg += role_readme(message.server.id)
	msg += 'Generators:\n'
	msg += generator.readme(conf.get_object(message.server.id, 'generators'))
	msg += 'Other commands:\n'
	msg += '* `!roll NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used. Examples: `!roll 1d6`, `!roll 2d20`, `!roll 1d20 3d6`.\n'
	msg += '* `!readme`: displays this helpful message.'
	await client.send_message(message.channel, msg)

def role_readme(server):
	msg = ''
	for roleset in conf.get_object(server, 'rolesets').keys():
		msg += '* `!list {0}`: Lists all roles in roleset {0}.\n'.format(roleset)
		msg += '* `!{0} <{0}name>`: You become the chosen {0}. Example: `!{0} {1}`\n'.format(roleset, [a for a in list(conf.get_object(server, 'rolesets', roleset).keys()) if a != 'removeOnUpdate'][0])
		if roleset != conf.get_object(server, 'defaultRoleset'):
			msg += '* `!{0} none`: Removes any roles you have from the {0} roleset.\n'.format(roleset)
	return msg

async def random_role(member, roleset):
	role = random.choice(get_roleset(member.server, roleset))
	await change_role(member, role.name, roleset)
	return role

async def add_role(member, role, roleset):
	log.debug('adding {0.name} to {1.name} on {2.name}'.format(role, member, member.server))
	roles = [role]
	if conf.get_object(member.server.id, 'rolesets', roleset, role.name) and 'secondaryRoles' in conf.get_object(member.server.id, 'rolesets', roleset, role.name):
		for roleName in conf.get_object(member.server.id, 'rolesets', roleset, role.name, 'secondaryRoles'):
			secondRole = discord.utils.find(lambda r: r.name.lower() == roleName.lower(),   member.server.roles)
			if secondRole not in member.roles:
				roles = roles + [secondRole]
	await client.add_roles(member, *roles)

def find_channel(channel_name, server):
	for x in server.channels:
		if x.name == channel_name:
			return x
	log.error('channel {0} not found on server {1.name}'.format(channel_name, server))

async def change_role(member, roleName, roleset):
	if any(role.name.lower() == roleName.lower() for role in get_roleset(member.server, roleset)):
		role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.server.roles)
		await client.remove_roles(member, *get_roles_to_remove(member.server, roleset))
		todo.append((member, [role, roleset]))
		return role
	else:
		raise NameError(roleName)

def get_roleset(server, roleset):
	roleNames = conf.get_object(server.id, 'rolesets', roleset).keys()
	validRoles = [x for x in server.roles if x.name in roleNames]
	return validRoles

def get_roles_to_remove(server, roleset):
	roles = get_roleset(server, roleset)
	if 'removeOnUpdate' in conf.get_object(server.id, 'rolesets', roleset):
		roles += [x for x in server.roles if x.name in conf.get_object(server.id, 'rolesets', roleset, 'removeOnUpdate')]
	return roles

client.run(TOKEN)
