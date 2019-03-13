import random
import re
import shelve
from collections import OrderedDict
from lark import Lark, Transformer

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
		for (baseKey, value) in list:
			key = baseKey
			iterator = 0
			while key in results:
				iterator += 1
				key = baseKey + ' (' + str(iterator) + ')'
			results[key] = value
		return results
	def roll(self, list):
		count = int(list[0])
		size = int(list[1])
		mod = 0
		try:
			mod = list[2]
		except:
			pass
		result = 0
		for i in range(count):
			result += random.randint(1, size) + mod
		name = str(count) + 'd' + str(size)
		if mod != 0:
			if mod > 0:
				name = name + '+' + str(mod)
			else:
				name = name + str(mod)
		return (name, result)
	def mod(self, list):
		return int(list[0]) * int(list[1])
	def sign(self, sign):
		if sign[0] == '+':
			return 1
		else:
			return -1
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
