import dateparser
import discord
import logging
import os
import random
import sys
import types
import yaml
from pathlib import Path

import automod
import botconfig as conf
import botdice as dice
import colors
import generator
import lmgtfy
import mediawiki
import pet
import reminder
import utils
import writesprint
import rep

utils.check_path('logs')

if len(sys.argv) > 1:
	botname = sys.argv[1]

conf.__init__('config.yaml', botname)

logging.basicConfig(
	filename='logs/{0}.log'.format(botname),
	format='%(asctime)s %(levelname)-8s %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
log = logging.getLogger('LongSphinx')

tokenfilename = f'{botname}.token'
COMMAND_CHAR = '!'
	
with open(tokenfilename, 'r') as tokenfile:
	TOKEN = tokenfile.readline().strip()

client = discord.Client()
commands = {}
is_reminder_set = False

def role_readme(server, **kwargs):
	msg = ''
	for roleset in conf.get_object(server, 'rolesets').keys():
		if conf.get_object(server, 'rolesets', roleset, 'type') == 'toggle':
			msg += f'* `!{roleset}`: List all toggleable {roleset} options.\n'
			msg += '* `!{0} <{0}name>`: You gain the chosen {0}. Use again to remove. Example: `!{0} {1}`\n'.format(roleset, next(a for a in list(conf.get_object(server, 'rolesets', roleset).keys()) if a != 'removeOnUpdate'))
		else:
			msg += f'* `!{roleset}`: Lists all available {roleset} options.\n'
			msg += '* `!{0} <{0}name>`: You become the chosen {0}. Other roles in this category are removed. Example: `!{0} {1}`\n'.format(roleset, next(a for a in list(conf.get_object(server, 'rolesets', roleset).keys()) if a != 'removeOnUpdate'))
			if roleset != conf.get_object(server, 'defaultRoleset'):
				msg += '* `!{0} none`: Removes any roles you have from the {0} roleset.\n'.format(roleset)
	if not msg:
		return 'No rolesets configured for this server.'
	return msg

async def give_help(user, client, channel, server, mentionTarget, command, argstring, conf, botname):
	if argstring in commands.keys():
		return commands[argstring][1](
			user=user,
			client=client,
			channel=channel,
			server=server,
			mentionTarget=mentionTarget,
			command=command,
			argstring=argstring,
			conf=conf,
			botname=botname)
	return 'Implemented commands: ' + ', '.join(commands.keys()) + '\nTry `!{0} <commandName>` to learn more.'.format(command)

def readme_readme(**kwargs):
	return 'pick a command that you need help with.'

async def channel_check(message, conf):
	if not message.server:
		return False
	if conf.get_object(message.server, 'channelListBehavior') == 'whitelist':
		if message.channel.name in conf.get_object(message.server, 'channels') or message.channel.id in conf.get_object(message.server, 'channels'):
			return False
		return True
	if message.channel.name not in conf.get_object(message.server, 'channels') and message.channel.id not in conf.get_object(message.server, 'channels'):
		return False
	return True

async def do_command(message, conf):
	if message.content.startswith(COMMAND_CHAR):
		command = message.content[1:].strip().lower()
		if utils.is_command(command, 'rerole'):
			await rerole(message)

		elif command.split()[0] in commands.keys() and commands[command.split()[0]][0]:
			try:
				argstring = command.split(maxsplit=1)[1]
			except IndexError:
				argstring = None
			if argstring and argstring.strip().lower() == 'help':
				argstring = command.split()[0]
				command = 'readme'
			result = await commands[command.split()[0]][0](
				user=message.author,
				client=client,
				channel=message.channel,
				server=message.server,
				mentionTarget=utils.getMentionTarget(message),
				command=command.split()[0],
				argstring=argstring,
				conf=conf,
				botname=botname
			)
			if type(result) is tuple:
				permissions = False
				try:
					permissions = message.channel.permissions_for(utils.find_self_member(client, message.server))
				except:
					pass
				if not permissions or permissions.embed_links:
					setEmbedColor(result[1], message.server)
					await client.send_message(message.channel, result[0], embed=result[1])
				else:
					reply = result[0] + '\n' + utils.embed_to_text(result[1])
					await client.send_message(message.channel, reply)
			else:
				await client.send_message(message.channel, result)
		else:
			msg = await parse(message)
			await client.send_message(message.channel, msg)

commands = {
	'remind': (reminder.message_reminder, reminder.readme),
	'color': (colors.show_swatch, colors.readme),
	'colour': (colors.show_swatch, colors.readme),
	'makesprint': (writesprint.make_sprint, writesprint.readme),
	'joinsprint': (writesprint.join_sprint, writesprint.readme),
	'sprintwords': (writesprint.record_words, writesprint.readme),
	'summon': (pet.summon, pet.readme),
	'feed': (pet.feed, pet.readme),
	'pet': (pet.pet, pet.readme),
	'getseed': (pet.getSeed, pet.readme),
	'rep': (rep.rep, rep.readme),
	'hep': (rep.rep, rep.readme),
	'duh': (lmgtfy.get_link, lmgtfy.readme),
	'lmgtfy': (lmgtfy.get_link, lmgtfy.readme),
	'saveroll': (dice.save_command, dice.readme),
	'search': (mediawiki.search, mediawiki.readme),
	'clearroll': (dice.clear_command, dice.readme),
	'gen': (generator.gen_as_text, generator.readme),
	'roll': (dice.roll_dice, dice.readme),
	'r': (dice.roll_dice, dice.readme),
	'rolls': (dice.list_rolls, dice.readme),
	'role': (None, role_readme),
	'readme': (give_help, readme_readme),
	'rtfm': (give_help, readme_readme),
	}

modules = [
	conf.update_config,
	automod.first_message_link,
	channel_check,
	do_command
	]

@client.event
async def on_message(message):
	if message.author != client.user:
		for module in modules:
			try:
				shouldAbort = await module(message=message, conf=conf)
				if shouldAbort:
					break
			except:
				log.exception('Exception in on_message:')

@client.event
async def on_ready():
	global is_reminder_set
	log.debug(f'Bot logged in as {client.user.name}')
	if not is_reminder_set:
		for server in client.servers:
			recurring = conf.get_object(server, 'recurring')
			if recurring:
				for event in recurring:
					await set_recurring_event(server, event)
		await reminder.set_all_saved_reminders(client, conf.bot_name())
		is_reminder_set = True
		print('Bot started')

@client.event
async def on_member_join(member):
	automod.add_to_noobs(member)
	channel = utils.find_channel(conf.get_object(member.server, 'greetingChannel'), member.server)
	log.debug(f'{member.name} joined {member.server}')
	if conf.get_object(member.server, 'defaultRoleset'):
		role = await random_role(member, conf.get_object(member.server, 'defaultRoleset'))
		msg = conf.get_string(member.server, 'welcome').format(member.mention, role.name)
	else:
		msg = conf.get_string(member.server, 'welcome').format(member.mention)
	await client.send_message(channel, msg)

@client.event
async def on_member_remove(member):
	channel = utils.find_channel(conf.get_object(member.server, 'leavingChannel'), member.server)
	if channel:
		msg = conf.get_string(member.server, 'left').format(member.name)
		await client.send_message(channel, msg)

async def parse(message):
	if conf.get_object(message.server, 'rolesets'):
		if len(message.author.roles) > 1:
			for roleset in conf.get_object(message.server, 'rolesets').keys():
				if utils.is_command(message.content, roleset):
					return await request_role(message, roleset)
	if conf.get_object(message.server, 'static'):
		for entry in conf.get_object(message.server, 'static').keys():
			if utils.is_command(message.content, entry):
				return await static_message(message, entry)

def setEmbedColor(embed, server):
	if embed.color == discord.Embed.Empty:
		embed.color = conf.get_object(server, 'embedColor')

async def request_role(message, roleset):
	words = message.content.split()[1:]
	if words and utils.is_command(words[0], roleset):
		words.pop()
	if len(words) == 0:
		return await list_roles(message, roleset)
	elif conf.get_object(message.server, 'rolesets', roleset)['type'] == 'toggle':
		return await toggle_role(message.author, ' '.join(words))
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
	log.debug(f'adding {role.name} to {member.name} on {member.server.name}')
	roles = [role]
	if conf.get_object(member.server, 'rolesets', roleset, 'roles', role.name) and 'secondaryRoles' in conf.get_object(member.server, 'rolesets', roleset, 'roles', role.name):
		for roleName in conf.get_object(member.server, 'rolesets', roleset, 'roles', role.name, 'secondaryRoles'):
			secondRole = discord.utils.find(lambda r: r.name.lower() == roleName.lower(),   member.server.roles)
			if secondRole not in member.roles:
				roles = roles + [secondRole]
	await client.add_roles(member, *roles)

async def change_role(member, roleName, roleset):
	if any(role.name.lower() == roleName.lower() for role in get_roleset(member.server, roleset)):
		role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.server.roles)
		to_remove = get_roles_to_remove(member.server, roleset)
		to_remove.remove(role)
		await client.remove_roles(member, *to_remove)
		await add_role(member, role, roleset)
		return role
	else:
		raise NameError(roleName)

async def toggle_role(member, roleName):
	role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.server.roles)
	if any(role.name.lower() == roleName.lower() for role in member.roles):
		await client.remove_roles(member, role)
		return conf.get_string(member.server, 'roleToggleOff').format(member.mention, role.name)
	else:
		await client.add_roles(member, role)
		return conf.get_string(member.server, 'roleToggleOn').format(member.mention, role.name)

async def set_scheduled_event(server, event):
	when_time = dateparser.parse(event['time'])
	channel = utils.find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_reminder(when_time, client, channel, msg)

async def set_recurring_event(server, event):
	channel = utils.find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_recurring_message(event['time'], client, channel, msg)

def get_roleset(server, roleset):
	roleNames = conf.get_object(server, 'rolesets', roleset, 'roles').keys()
	validRoles = [x for x in server.roles if x.name in roleNames]
	return validRoles

def get_randomables(server, roleset):
	roleNames = conf.get_object(server, 'rolesets', roleset, 'roles')
	roles = [k for k,v in roleNames.items() if not v or 'random' not in v or v['random']]
	validRoles = [x for x in server.roles if x.name in roles]
	return validRoles
	
def get_roles_to_remove(server, roleset):
	roles = get_roleset(server, roleset)
	if 'removeOnUpdate' in conf.get_object(server, 'rolesets', roleset):
		roles += [x for x in server.roles if x.name in conf.get_object(server, 'rolesets', roleset, 'removeOnUpdate')]
	return roles

def strip_command(argstring, command):
	return argstring[(len(command)+2):]
client.run(TOKEN)
