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
import reactor

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

async def give_help(user, channel, server, mentionTarget, command, argstring, conf, botname):
	if argstring in commands.keys():
		return commands[argstring][1](
			user=user,
			channel=channel,
			server=server,
			mentionTarget=mentionTarget,
			command=command,
			argstring=argstring,
			conf=conf,
			botname=botname)
	elif conf.get_object(server, 'rolesets') and argstring in conf.get_object(server, 'rolesets').keys():
		return await list_roles(server, channel, argstring)
	return 'Implemented commands: ' + ', '.join(commands.keys()) + '\nTry `!{0} <commandName>` to learn more.'.format(command)

def readme_readme(**kwargs):
	return 'pick a command that you need help with.'

async def channel_check(message, conf, **kwargs):
	if not message.guild:
		return False
	if conf.get_object(message.guild, 'channelListBehavior') == 'whitelist':
		if message.channel.name in conf.get_object(message.guild, 'channels') or message.channel.id in conf.get_object(message.guild, 'channels'):
			return False
		return True
	if message.channel.name not in conf.get_object(message.guild, 'channels') and message.channel.id not in conf.get_object(message.guild, 'channels'):
		return False
	return True

async def do_command(message, conf, **kwargs):
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
				channel=message.channel,
				server=message.guild,
				mentionTarget=utils.getMentionTarget(message),
				command=command.split()[0],
				argstring=argstring,
				conf=conf,
				botname=botname
			)
			if type(result) is tuple:
				permissions = False
				try:
					permissions = message.channel.permissions_for(utils.find_self_member(client, message.guild))
				except:
					pass
				if not permissions or permissions.embed_links:
					setEmbedColor(result[1], message.guild)
					await message.channel.send(result[0], embed=result[1])
				else:
					reply = result[0] + '\n' + utils.embed_to_text(result[1])
					await message.channel.send(reply)
			else:
				await message.channel.send(result)
		else:
			msg = await parse(message)
			await message.channel.send(msg)

commands = {
	'remind': (reminder.message_reminder, reminder.readme),
	'reminders': (reminder.list_my_reminders, reminder.readme),
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
	automod.no_role_link,
	channel_check,
	reactor.autoreact,
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
		for server in client.guilds:
			recurring = conf.get_object(server, 'recurring')
			if recurring:
				for event in recurring:
					await set_recurring_event(server, event)
		await reminder.set_all_saved_reminders(conf.bot_name(), client)
		is_reminder_set = True
		print('Bot started')

@client.event
async def on_member_join(member):
	automod.add_to_noobs(member)
	channel = utils.find_channel(conf.get_object(member.guild, 'greetingChannel'), member.guild)
	log.debug(f'{member.name} joined {member.guild}')
	if conf.get_object(member.guild, 'defaultRoleset'):
		role = await random_role(member, conf.get_object(member.guild, 'defaultRoleset'))
		msg = conf.get_string(member.guild, 'welcome').format(member.mention, role.name)
	else:
		msg = conf.get_string(member.guild, 'welcome').format(member.mention)
	await channel.send(msg)

@client.event
async def on_member_remove(member):
	channel = utils.find_channel(conf.get_object(member.guild, 'leavingChannel'), member.guild)
	if channel:
		msg = conf.get_string(member.guild, 'left').format(member.name)
		await channel.send(msg)

async def parse(message):
	if conf.get_object(message.guild, 'rolesets'):
		if len(message.author.roles) > 1:
			for roleset in conf.get_object(message.guild, 'rolesets').keys():
				if utils.is_command(message.content, roleset):
					return await request_role(message, roleset)
	if conf.get_object(message.guild, 'static'):
		for entry in conf.get_object(message.guild, 'static').keys():
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
		return await list_roles(message.guild, message.channel, roleset)
	elif words[0].lower() == 'none' and roleset != conf.get_object(message.guild, 'defaultRoleset'):
		await message.author.remove_roles(*get_roles_to_remove(message.author.guild, roleset))
		msg = conf.get_string(message.guild, 'roleClear').format(message.author.mention, roleset)
	elif conf.get_object(message.guild, 'rolesets', roleset)['type'] == 'toggle':
		return await toggle_role(message.author, ' '.join(words))
	else:
		try:
			newRole = await change_role(message.author, ' '.join(words), roleset)
			msg = conf.get_string(message.guild, 'roleChange').format(message.author.mention, newRole.name)
		except (NameError):
			msg = conf.get_string(message.guild, 'invalid' + roleset).format(message.author.mention, ' '.join(words))
	msg = generator.fix_articles(msg)
	await message.channel.send(msg)

async def list_roles(server, channel, roleset):
	roles = [x.name for x in get_roleset(server, roleset)]
	roles.sort()
	msg = conf.get_string(server, roleset + 'RoleList').format(', '.join(roles))
	await channel.send(msg)

	p = Path('.')
	filename = server.id + '_' + roleset + '.png'
	imagePath = p / 'roleImages' / filename
	await channel.send(file=discord.File(str(imagePath)))

async def static_message(message, value):
	msg = conf.get_object(message.guild, 'static', value)
	if msg.startswith('http'):
		embed = discord.Embed().set_image(url=msg)
		return await message.channel.send('', embed=embed)
	else:
		return await message.channel.send(msg)

async def rerole(message):
	role = await random_role(message.author, conf.get_object(message.guild, 'defaultRoleset'))
	msg = conf.get_string(message.guild, 'rerole').format(message.author.mention, role.name)
	await message.channel.send(msg)

async def random_role(member, roleset):
	role = random.choice(get_randomables(member.guild, roleset))
	await change_role(member, role.name, roleset)
	return role

async def add_role(member, role, roleset):
	log.debug(f'adding {role.name} to {member.name} on {member.guild.name}')
	roles = [role]
	if conf.get_object(member.guild, 'rolesets', roleset, 'roles', role.name) and 'secondaryRoles' in conf.get_object(member.guild, 'rolesets', roleset, 'roles', role.name):
		for roleName in conf.get_object(member.guild, 'rolesets', roleset, 'roles', role.name, 'secondaryRoles'):
			secondRole = discord.utils.find(lambda r: r.name.lower() == roleName.lower(),   member.guild.roles)
			if secondRole not in member.roles:
				roles = roles + [secondRole]
	await member.add_roles(*roles)

async def change_role(member, roleName, roleset):
	if any(role.name.lower() == roleName.lower() for role in get_roleset(member.guild, roleset)):
		role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.guild.roles)
		to_remove = get_roles_to_remove(member.guild, roleset)
		to_remove.remove(role)
		await member.remove_roles(*to_remove)
		await add_role(member, role, roleset)
		return role
	else:
		raise NameError(roleName)

async def toggle_role(member, roleNames):
	roleNameList = roleNames.lower().split()
	responses = []
	for roleName in roleNameList:
		role = discord.utils.find(lambda r: r.name.lower() == roleName.lower(), member.guild.roles)
		if any(role.name.lower() == roleName.lower() for role in member.roles):
			await member.remove_roles(role)
			responses.append(conf.get_string(member.guild, 'roleToggleOff').format(member.mention, role.name))
		else:
			await member.add_roles(role)
			responses.append(conf.get_string(member.guild, 'roleToggleOn').format(member.mention, role.name))
	return '\n'.join(responses)

async def set_scheduled_event(server, event):
	when_time = dateparser.parse(event['time'])
	channel = utils.find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_reminder(when_time, channel, msg)

async def set_recurring_event(server, event):
	channel = utils.find_channel(event['channel'], server)
	msg = event['message']
	await reminder.set_recurring_message(event['time'], channel, msg)

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
