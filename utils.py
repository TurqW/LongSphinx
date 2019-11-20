import os

fullGaugeChar = '='
emptyGaugeChar = ' '

def check_path(name):
	if not os.path.exists(name):
		os.makedirs(name)

def drawGauge(value, max):
	return '[' + fullGaugeChar*value + emptyGaugeChar*(max-value) + ']'

def getMentionTarget(message):
	if len(message.mentions) < 1:
		return message.author
	elif len(message.mentions) > 1:
		raise ValueError("Too many people tagged")
	else:
		return message.mentions[0]

def is_command(mystring, command):
	mystring = mystring.strip(' !')
	if mystring.split()[0].lower() == command.lower():
		return True
	return False