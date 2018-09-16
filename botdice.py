import random

def parse_die(com):
	return [int(s) for s in com.strip().split('d')]

def roll_dice(parsed):
	results = []
	for i in range(parsed[0]):
		results.append(random.randint(1, parsed[1]))
	return results

def roll_command(command):
	# TODO modifiers, handle "+" etc, advantage?
	if not command:
		command = ['1d20']
	res = []
	for com in command:
		res = res + roll_dice(parse_die(com))
	return res

