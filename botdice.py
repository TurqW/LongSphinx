import random
import re
import discord
from collections import OrderedDict
from lark import Lark, Transformer
from lark.exceptions import LarkError
from botdb import BotDB

dbname = 'macros'

parser = Lark(r"""
%import common.WS
%ignore WS
%import common.DIGIT
%import common.INT

NZDIGIT : "1".."9"
POSINT : DIGIT* NZDIGIT DIGIT*
sign : /[+-]/
rollset : expression ("," expression)*
expression : die -> roll
			| POSINT -> mod
			| expression sign expression -> math
die : [POSINT] _DSEPARATOR POSINT
count : POSINT
size : POSINT
_DSEPARATOR : "d"
""", start='rollset')

class RollsetTransformer(Transformer):
	def rollset(self, list):
		results = OrderedDict()
		for item in list:
			key = item['name']
			iterator = 0
			while key in results:
				iterator += 1
				key = item['name'] + ' (' + str(iterator) + ')'
			if '+' not in item['description']:
				results[key] = '**' + str(item['value']) + '**'
			else:
				results[key] = item['description'] + ' = **' + str(item['value']) + '**'
		return results


	def die(self, list):
		try:
			count = int(list[0])
			size = int(list[1])
		except IndexError:
			count = 1
			size = int(list[0])
		if count > 1000:
			raise Exception('Too many dice, blocking to avoid DDOS')
		results = []
		for i in range(count):
			results.append(random.randint(1, size))
		description = '(' + '+'.join([str(i) for i in results]) + ')'
		name = str(count) + 'd' + str(size)
		return {'name': name, 'description': description, 'value': sum(results)}

	def roll(self, list):
		return list[0]

	def math(self, list):
		name = "".join([a['name'] for a in list])
		description = "".join([a['description'] for a in list])
		value = list[0]['value'] + list[1]['value'] * list[2]['value']
		return {'name': name, 'description': description, 'value': value}

	def mod(self, num):
		return {'name': num[0], 'description': num[0], 'value': int(num[0])}

	def sign(self, sign):
		if sign[0] == '+':
			return {'name': '+', 'description': '+', 'value': 1}
		else:
			return {'name': '-', 'description': '-', 'value': -1}

	def POSINT(self, num):
		return int(num[0])

	def INT(self, num):
		return int(num[0])

def roll_command(user, command):
	if not command:
		command = 'd20'
	try:
		name = ''
		if ':' in command:
			command, name = command.split(':')
			name = name.strip()
		with BotDB(dbname, botName) as db:
			macros = db[user]
			for key in sorted(macros.keys(), key=len):
				# For prefix matching, you want to match to the shortest possible match so all matches can be hit
				if key.startswith(command.lower()):
					if not name:
						name = key
					command = macros[key]
	except:
		#TODO this should be way more specific
		pass
	return name, RollsetTransformer().transform(parser.parse(command))

async def save_command(user, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	command, name = [i.strip().lower() for i in argstring.split(':')]
	try:
		parser.parse(command)
	except LarkError:
		return 'Command was not valid.'
	if any(char.isdigit() for char in name) or name.strip().lower() == 'help':
		return 'Name was not valid.'
	with BotDB(dbname, botName) as db:
		if user.id not in db:
			db[user.id] = {name: command}
		else:
			newVersion = db[user.id]
			newVersion[name] = command
			db[user.id] = newVersion
	return user.mention + ' has saved ' + command + ' as ' + name.lower()

async def clear_command(user, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	name = argstring.strip()
	with BotDB(dbname, botName) as db:
		if user.id in db:
			newVersion = db[user.id]
			newVersion.pop(name.lower())
			db[user.id] = newVersion
	return user.mention + ' has deleted saved roll ' + name.lower()

def list_commands(user):
	try:
		with BotDB(dbname, botName) as db:
			return db[user]
	except KeyError:
		return {}

async def roll_dice(user, client, channel, server, mentionTarget, command, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	try:
		embed = discord.Embed()
		name, results = roll_command(str(user.id), argstring)
		for key, value in results.items():
			embed.add_field(name=key, value=value)
		if name:
			embed.title = name
		else:
			name = argstring
		msg = user.mention + ' rolled ' + name + '!'
	except Exception as e:
		return str(e)
	return msg, embed

async def list_rolls(user, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	embed = discord.Embed()
	for key, value in sorted(list_commands(str(user.id)).items()):
		embed.add_field(name=key, value=value)
	return user.mention + ' has these saved rolls.', embed

def stringy_mod(modifier):
	if modifier > 0:
		return '+' + str(modifier)
	if modifier < 0:
		return str(modifier)
	return ''

def readme(**kwargs):
	return '''* `!roll NdM` or `!r NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used.
> Examples: `!roll 1d6`, `!roll 2d20+3`, `!roll 1d20, 3d6`.
* `!saveroll NdM: rollname`: saves NdM as rollname, so that you can roll it with just `!roll rollname`.
> Example: `!saveroll 1d20+5,1d8+3: hammer`
* `!rolls`: shows your saved rolls.
* `!clearroll rollname`: deletes a saved roll. There is no undo button.\n'''
