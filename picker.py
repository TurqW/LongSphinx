import logging
import random

log = logging.getLogger('LongSphinx.Generators')

async def pick(argstring, roleMentions, **kwargs):
	toPick = 1
	if argstring.split(' ', 1)[0].isnumeric():
		toPick = int(argstring.split(' ', 1)[0])
		argstring = argstring.split(' ', 1)[1]
	if ',' in argstring:
		options = argstring.split(',')
	else:
		options = argstring.split()
	if len(roleMentions) > 0:
		options = [member.mention for member in roleMentions[0].members]
	if toPick < 1:
		return "Zoinks! I can't pick less than one."
	if toPick > len(options):
		toPick = len(options)
	return 'I have chosen: ' + ', '.join(random.sample(options, toPick))

def readme(**kwargs):
	return """Picker:
* `!pick thing1 thing2 thing3 thing4`: Randomly picks one of the things.
* `!pick 2 good, fast, cheap`: Randomly picks two of the things. No repetition, order is random.
* `!pick @role`: Randomly picks a member with that role. Numbers can be used here too.
Commas between options are required if you have multi-word options, optional otherwise. If you use any commas, you must have commas between every option.
"""