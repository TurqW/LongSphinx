import random
import re

def parse_die(com): #TODO: may replace this whole thing with an actual grammar/parser
	print(com)
	print('new entry')
	countString, sideString = com.strip().split('d')
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

def roll_command(command):
	if not command:
		command = 'd20'
	command = command.replace(' ', '')
	return {com : roll_dice(parse_die(com)) for com in command.split(',')}

def stringy_mod(modifier):
	if modifier > 0:
		return '+' + str(modifier)
	if modifier < 0:
		return str(modifier)
	return ''

def readme():
	return '* `!roll NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used. Examples: `!roll 1d6`, `!roll 2d20`, `!roll 1d20 3d6`.\n'
