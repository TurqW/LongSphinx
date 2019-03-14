import random
import re
import shelve
from collections import OrderedDict
from lark import Lark, Transformer
from lark.exceptions import LarkError

dbname = 'data/macros'

parser = Lark(r"""
%import common.WS
%ignore WS
%import common.DIGIT
%import common.INT

NZDIGIT : "1".."9"
POSINT : DIGIT* NZDIGIT DIGIT*
sign : /[+-]/
mod : (sign) INT
rollset : roll ("," roll)*
roll : POSINT _DSEPARATOR POSINT [mod]
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
			results[key] = item['description']
		return results
	def roll(self, list):
		count = int(list[0])
		size = int(list[1])
		mod = {'name': '', 'value': 0}
		try:
			mod = list[2]
		except:
			pass
		results = []
		for i in range(count):
			results.append(random.randint(1, size))
		description = '(' + '+'.join([str(i) for i in results]) + ')' + mod['name'] + '=' + str(sum(results) + mod['value'])
		name = str(count) + 'd' + str(size) + mod['name']
		return {'name': name, 'description': description}
	def mod(self, list):
		return {'name': list[0]['name'] + str(list[1]), 'value': list[0]['value'] * int(list[1])}
	def sign(self, sign):
		if sign[0] == '+':
			return {'name': '+', 'value': 1}
		else:
			return {'name': '-', 'value': -1}
	def POSINT(self, num):
		return int(num[0])
	def INT(self, num):
		return int(num[0])

def roll_command(user, command):
	if not command:
		command = 'd20'
	try:
		with shelve.open(dbname) as db:
			command = db[user][command.lower()]
	except KeyError:
		pass
	return RollsetTransformer().transform(parser.parse(command))

def save_command(user, input):
	command, name = [i.strip().lower() for i in input.split(':')]
	try:
		parser.parse(command)
	except LarkError:
		raise Exception('Command was not valid.')
	if any(char.isdigit() for char in name):
		raise Exception('Name was not valid.')
	with shelve.open(dbname) as db:
		if user not in db:
			db[user] = {name: command}
		else:
			newVersion = db[user]
			newVersion[name] = command
			db[user] = newVersion
	return command, name

def clear_command(user, input):
	name = input.strip()
	with shelve.open(dbname) as db:
		if user in db:
			newVersion = db[user]
			newVersion.pop(name.lower())
			db[user] = newVersion
	return name

def list_commands(user):
	try:
		with shelve.open(dbname) as db:
			return db[user]
	except KeyError:
		return {}

def stringy_mod(modifier):
	if modifier > 0:
		return '+' + str(modifier)
	if modifier < 0:
		return str(modifier)
	return ''

def readme():
	return '* `!roll NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used. Examples: `!roll 1d6`, `!roll 2d20`, `!roll 1d20 3d6`.\n'
