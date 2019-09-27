import dateparser
import discord
import logging
import os
import random
import re
import sys
import types
import yaml
from pathlib import Path

import botconfig as conf
import botdice as dice
import colors
import generator
import lmgtfy
import pet
import reminder
import utils
import writesprint

utils.check_path('logs')

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
commands = {}
noobs = []

def role_readme(server, **kwargs):
	msg = ''
	for roleset in conf.get_object(server, 'rolesets').keys():
		msg += '* `!{0}`: Lists all roles in roleset {0}.\n'.format(roleset)
		msg += '* `!{0} <{0}name>`: You become the chosen {0}. Example: `!{0} {1}`\n'.format(roleset, [a for a in list(conf.get_object(server, 'rolesets', roleset).keys()) if a != 'removeOnUpdate'][0])
		if roleset != conf.get_object(server, 'defaultRoleset'):
			msg += '* `!{0} none`: Removes any roles you have from the {0} roleset.\n'.format(roleset)
	return msg

async def give_help(user, client, channel, server, mentionTarget, command, input, conf):
	if input in commands.keys():
		return commands[input][1](
			user=user,
			client=client,
			channel=channel,
			server=server,
			mentionTarget=mentionTarget,
			command=command,
			input=input,
			conf=conf)
	return 'Implemented commands: ' + ', '.join(commands.keys()) + '\nTry `!readme <commandName>` to learn more.'

def readme_readme(**kwargs):
	return 'pick a command that you need help with.'

commands = {
	'remind': (reminder.message_reminder, reminder.readme),
	'color': (colors.show_swatch, colors.readme),
	'makesprint': (writesprint.make_sprint, writesprint.readme),
	'joinsprint': (writesprint.join_sprint, writesprint.readme),
	'sprintwords': (writesprint.record_words, writesprint.readme),
	'summon': (pet.summon, pet.readme),
	'feed': (pet.feed, pet.readme),
	'pet': (pet.pet, pet.readme),
	'getseed': (pet.getSeed, pet.readme),
	'duh': (lmgtfy.get_link, lmgtfy.readme),
	'lmgtfy': (lmgtfy.get_link, lmgtfy.readme),
	'saveroll': (dice.save_command, dice.readme),
	'clearroll': (dice.clear_command, dice.readme),
	'gen': (generator.gen_as_text, generator.readme),
	'roll': (dice.roll_dice, dice.readme),
	'rolls': (dice.list_rolls, dice.readme),
	'role': (None, role_readme),
	'readme': (give_help, readme_readme),
	'rtfm': (give_help, readme_readme),
	}

@client.event
async def on_message(message):
	for member, roleinfo in todo:
		try:
			await add_role(member, roleinfo[0], roleinfo[1])
		except discord.errors.NotFound:
			# If they've already left, we want to know, but to remove it from todo
			log.info('Member {0.name} not found on server {0.server}'.format(member))
	todo.clear()
	conf.update_config()
	# we do not want the bot to reply to itself
	if message.author == client.user:
		return
	automod = conf.get_object(message.server, 'automod')
	if automod and (message.server.id, message.author.id) in noobs:
		if re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
			role = discord.utils.find(lambda r: r.name.lower() == automod['role'].lower(), message.server.roles)
			dungeon_channel = find_channel(automod['channel'], message.server)
			await client.add_roles(message.author, role)
			await client.send_message(dungeon_channel, message.author.mention + ', your first message on the server was auto-flagged as potential spam. A mod will be here shortly to review your case. Your message: ```\n' + message.content + '\n```')
			try:
				await client.delete_message(message)
			except Exception as e:
				print(e)
		noobs.remove((message.server.id, message.author.id))
	try:
		if not message.server or message.channel.name in conf.get_object(message.server, 'channels') or message.channel.id in conf.get_object(message.server, 'channels'):
			if message.content.startswith(COMMAND_CHAR):
				command = message.content[1:].strip().lower()
				if isCommand(command, 'rerole'):
					await rerole(message)

				elif command.split()[0] in commands.keys():
					try:
						input = message.content.split(maxsplit=1)[1]
					except IndexError:
						input = None
					result = await commands[command.split()[0]][0](
						user=message.author,
						client=client,
						channel=message.channel,
						server=message.server,
						mentionTarget=utils.getMentionTarget(message),
						command=message.content.split()[0][1:],
						input=input,
						conf=conf
					)
					if type(result) is tuple:
						await client.send_message(message.channel, result[0], embed=result[1])
					else:
						await client.send_message(message.channel, result)
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
	for server in client.servers:
		schedule = conf.get_object(server, 'scheduled')
		for event in schedule:
			await set_scheduled_event(server, event)
	for server in client.servers:
		recurring = conf.get_object(server, 'recurring')
		for event in recurring:
			await set_recurring_event(server, event)

@client.event
async def on_member_join(member):
	noobs.append((member.server.id, member.id))
	channel = find_channel(conf.get_object(member.server, 'greetingChannel'), member.server)
	log.debug('{0.name} joined {0.server}'.format(member))
	if conf.get_object(member.server, 'defaultRoleset'):
		role = await random_role(member, conf.get_object(member.server, 'defaultRoleset'))
		msg = conf.get_string(member.server, 'welcome').format(member.mention, role.name)
	else:
		msg = conf.get_string(member.server, 'welcome').format(member.mention)
	await client.send_message(channel, msg)

@client.event
async def on_member_remove(member):
	channel = find_channel(conf.get_object(member.server, 'leavingChannel'), member.server)
	if channel:
		msg = conf.get_string(member.server, 'left').format(member.mention)
		await client.send_message(channel, msg)

async def parse(message):
	if conf.get_object(message.server, 'rolesets'):
		for roleset in conf.get_object(message.server, 'rolesets').keys():
			if isCommand(message.content, roleset):
				return await request_role(message, roleset)
	if conf.get_object(message.server, 'static'):
		for entry in conf.get_object(message.server, 'static').keys():
			if isCommand(message.content, entry):
				return await static_message(message, entry)

def isCommand(mystring, command):
	mystring = mystring.strip(' !')
	if mystring.split()[0].lower() == command.lower():
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

async def static_message(message, value):
	msg = conf.get_object(message.server, 'static', value)
	if msg.startswith('http'):
		embed = discord.Embed().set_image(url=msg)
		return await client.send_message(message.channel, '', embed=embed)
	else:
		return await client.send_message(message.channel, msg)

async def rerole(message):
	role = await random_role(message.author, conf.get_object(message.server, 'defaultRoleset'))
	msg = conf.get_string(message.server, 'rerole').format(message.author.mention, role.name)
	await client.send_message(message.channel, msg)

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

async def set_scheduled_event(server, event):
	when_time = dateparser.parse(event['time'])
	channel = find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_reminder(when_time, client, channel, msg)

async def set_recurring_event(server, event):
	channel = find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_recurring_message(event['time'], client, channel, msg)

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

def strip_command(input, command):
	return input[(len(command)+2):]
client.run(TOKEN)
