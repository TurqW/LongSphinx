import random

def parse_die(com):
	return [int(s) for s in com.strip().split('d')]

def roll_dice(parsed):
	results = []
	for i in range(parsed[0]):
		results.append(random.randint(1, parsed[1]))
	return results

def roll_command(command):
	if not command:
		command = ['1d20']
	res = []
	for com in command:
		res = res + roll_dice(parse_die(com))
	return res

def readme():
	return '* `!roll NdM`: rolls a `M`-sided die `N` times. Multiple sets of dice can be used. Examples: `!roll 1d6`, `!roll 2d20`, `!roll 1d20 3d6`.\n'
