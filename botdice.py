import random
import re
import shelve

dbname = 'data/macros'

def parse_die(com): #TODO: may replace this whole thing with an actual grammar/parser
	try:
		countString, sideString = com.strip().split('d')
	except:
		raise ValueError(com + ' is not a valid dice roll.')
	try:
		count = int(countString)
	except:
		count = 1

	modifier = 0
	if ('+' in sideString or '-' in sideString):
		sides, modifier = [int(s) for s in re.split('[+-]', sideString)]
		if ('-' in sideString):
			modifier = -1*modifier
	else:
		sides = int(sideString)
	return [count, sides, modifier]

def roll_dice(parsed):
	results = []
	if parsed[0] <= 1000:
		for i in range(parsed[0]):
			results.append(random.randint(1, parsed[1]))
	else:
		raise ValueError('Oh come on, do you really need more than 1000 dice?')
	description = '(' + '+'.join([str(i) for i in results]) + ')' + stringy_mod(parsed[2]) + '=' + str(sum(results) + parsed[2])
	return description

def roll_command(user, command):
	if not command:
		command = 'd20'
	with shelve.open(dbname) as db:
		if command in db[user]:
			command = db[user][command]
		print(db[user])
	command = command.replace(' ', '')
	print(command)
	return {com : roll_dice(parse_die(com)) for com in command.split(',')}

def save_command(user, input):
	command, name = [i.strip() for i in input.split(':')]
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
			newVersion.pop(name)
			db[user] = newVersion
	return name

def stringy_mod(modifier):
	if modifier > 0:
		return '+' + str(modifier)
	if modifier < 0:
		return str(modifier)
	return ''

def readme():
	return '* `!roll NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used. Examples: `!roll 1d6`, `!roll 2d20`, `!roll 1d20 3d6`.\n'
