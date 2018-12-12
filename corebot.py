import discord
import random
import yaml
import sys
import logging
import nltk
import os
from pathlib import Path



import generator
import botconfig as conf
import botdice as dice
import reminder
import colors
import pet

def check_path(name):
	if not os.path.exists(name):
		os.makedirs(name)
check_path("logs")
check_path("data")

logging.basicConfig(filename='logs/ubeast.log',level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
log = logging.getLogger('LongSphinx')

tokenfilename = 'token.txt'
COMMAND_CHAR = '!'

if len(sys.argv) > 1:
	tokenfilename = sys.argv[1]
	
with open(tokenfilename, 'r') as tokenfile:
	TOKEN = tokenfile.readline().strip()

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

	try:
		if not message.server or message.channel.name in conf.get_object(message.server, 'channels'):
			if message.content.startswith(COMMAND_CHAR):
				command = message.content[1:].strip()
				if isCommand(command, 'roll'):
					#dice
					await roll_dice(message)

				elif isCommand(command, 'rerole'):
					await rerole(message)

				elif isCommand(command, 'readme'):
					await give_help(message)

				elif isCommand(command, 'remind'):
					await set_reminder(message)
				
				elif isCommand(command, 'feed'):
					await client.send_message(message.channel, pet.feed())

				elif isCommand(command, 'pet'):
					await client.send_message(message.channel, pet.pet())

				elif isCommand(command, 'color'):
					await show_swatch(message)
				
				else:
					await parse(message)
			elif message.content.startswith('&join'):
				await on_member_join(message.author)
			elif message.content.startswith('<:Tim:'):
				await client.send_message(message.channel, 'You rang?')
	except:
		log.exception('Exception in on_message:')

@client.event
async def on_ready():
	log.debug('Bot logged in as {0.user.name}'.format(client))
	print('Bot started')

@client.event
async def on_member_join(member):
	channel = find_channel(conf.get_object(member.server, 'greetingChannel'), member.server)
	log.debug('{0.name} joined {0.server}'.format(member))
	if conf.get_object(member.server, 'defaultRoleset'):
		role = await random_role(member, conf.get_object(member.server, 'defaultRoleset'))
		msg = conf.get_string(member.server, 'welcome').format(member.mention, role.name)
	else:
		msg = conf.get_string(member.server, 'welcome').format(member.mention)
	await client.send_message(channel, msg)

async def parse(message):
	if conf.get_object(message.server, 'rolesets'):
		for roleset in conf.get_object(message.server, 'rolesets').keys():
			if isCommand(message.content, roleset):
				return await request_role(message, roleset)
	for gen in conf.get_object(message.server, 'generators'):
		if isCommand(message.content, gen):
			msg = message.author.mention +', ' + generator.generate(gen)
			return await client.send_message(message.channel, msg)
	if conf.get_object(message.server, 'static'):
		for entry in conf.get_object(message.server, 'static').keys():
			if isCommand(message.content, entry):
				return await static_message(message, entry)

def isCommand(mystring, command):
	mystring = mystring.strip(' !')
	p = nltk.PorterStemmer()
	if p.stem(mystring.split()[0]) == p.stem(command):
		return True
	return False

async def request_role(message, roleset):
	words = message.content.split()[1:]
	if words and isCommand(words[0], roleset):
		words.pop()
	if len(words) == 0:
		return await list_roles(message, roleset)
	elif words[0].lower() == 'none' and roleset != conf.get_object(message.server, 'defaultRoleset'):
		await client.remove_roles(message.author, *get_roles_to_remove(message.author.server, roleset))
		msg = conf.get_string(message.server, 'roleClear').format(message.author.mention, roleset)
	else:
		try:
			newRole = await change_role(message.author, ' '.join(words), roleset)
			msg = conf.get_string(message.server, 'roleChange').format(message.author.mention, newRole.name)
		except (NameError):
			msg = conf.get_string(message.server, 'invalid' + roleset).format(message.author.mention, ' '.join(words))
	msg = generator.fix_articles(msg)
	await client.send_message(message.channel, msg)

async def list_roles(message, roleset):
	roles = [x.name for x in get_roleset(message.server, roleset)]
	roles.sort()
	msg = conf.get_string(message.server, roleset + 'RoleList').format(', '.join(roles))
	await client.send_message(message.channel, msg)

	p = Path('.')
	filename = message.server.id + '_' + roleset + '.png'
	imagePath = p / 'roleImages' / filename
	await client.send_file(message.channel, str(imagePath))

async def show_swatch(message):
	color = message.content.split()[1]
	log.error(color)
	swatch = colors.get_swatch(color)
	await client.send_file(message.channel, swatch, filename=color + '.png')

async def static_message(message, value):
	msg = conf.get_object(message.server, 'static', value)
	if msg.startswith('http'):
		embed = discord.Embed().set_image(url=msg)
		return await client.send_message(message.channel, '', embed=embed)
	else:
		return await client.send_message(message.channel, msg)

async def roll_dice(message):
	toRoll = message.content.split()
	results = dice.roll_command(toRoll[1:])
	resultString = ', '.join([str(i) for i in results])
	msg = conf.get_string(message.server, 'diceResults').format(message.author.mention, resultString, sum(results))
	try:
		await client.send_message(message.channel, msg)
	except discord.errors.HTTPException:
		msg = conf.get_string(message.server, 'diceResults').format(message.author.mention, 'they show many numbers', sum(results))
		await client.send_message(message.channel, msg)

async def rerole(message):
	role = await random_role(message.author, conf.get_object(message.server, 'defaultRoleset'))
	msg = conf.get_string(message.server, 'rerole').format(message.author.mention, role.name)
	await client.send_message(message.channel, msg)

async def give_help(message):
	msg = ''
	if conf.get_object(message.server, 'rolesets'):
		msg += 'Role operations:\n'
		msg += role_readme(message.server)
	msg += 'Generators:\n'
	msg += generator.readme(conf.get_object(message.server, 'generators'))
	msg += 'Other commands:\n'
	msg += dice.readme()
	msg += colors.readme()
	msg += '* `!readme`: displays this helpful message.'
	await client.send_message(message.channel, msg)

def role_readme(server):
	msg = ''
	for roleset in conf.get_object(server, 'rolesets').keys():
		msg += '* `!{0}`: Lists all roles in roleset {0}.\n'.format(roleset)
		msg += '* `!{0} <{0}name>`: You become the chosen {0}. Example: `!{0} {1}`\n'.format(roleset, [a for a in list(conf.get_object(server, 'rolesets', roleset).keys()) if a != 'removeOnUpdate'][0])
		if roleset != conf.get_object(server, 'defaultRoleset'):
			msg += '* `!{0} none`: Removes any roles you have from the {0} roleset.\n'.format(roleset)
	return msg

async def random_role(member, roleset):
	role = random.choice(get_randomables(member.server, roleset))
	await change_role(member, role.name, roleset)
	return role

async def add_role(member, role, roleset):
	log.debug('adding {0.name} to {1.name} on {2.name}'.format(role, member, member.server))
	roles = [role]
	if conf.get_object(member.server, 'rolesets', roleset, role.name) and 'secondaryRoles' in conf.get_object(member.server, 'rolesets', roleset, role.name):
		for roleName in conf.get_object(member.server, 'rolesets', roleset, role.name, 'secondaryRoles'):
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

async def set_reminder(message):
	await reminder.create_reminder(' '.join(message.content.split()[1:]), client, message.channel, 'reminder: {0}'.format(message.content))

def get_roleset(server, roleset):
	roleNames = conf.get_object(server, 'rolesets', roleset).keys()
	validRoles = [x for x in server.roles if x.name in roleNames]
	return validRoles

def get_randomables(server, roleset):
	roleNames = conf.get_object(server, 'rolesets', roleset)
	roles = [k for k,v in roleNames.items() if not v or 'random' not in v or v['random']]
	validRoles = [x for x in server.roles if x.name in roles]
	return validRoles
	
def get_roles_to_remove(server, roleset):
	roles = get_roleset(server, roleset)
	if 'removeOnUpdate' in conf.get_object(server, 'rolesets', roleset):
		roles += [x for x in server.roles if x.name in conf.get_object(server, 'rolesets', roleset, 'removeOnUpdate')]
	return roles

client.run(TOKEN)
