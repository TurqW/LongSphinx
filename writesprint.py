import asyncio
import datetime
import logging
import re
from collections import ChainMap
from lark import Lark, Transformer
from lark.exceptions import LarkError
from botdb import BotDB
log = logging.getLogger('LongSphinx.WriteSprint')

dbname = 'sprints'
DEFAULT_DURATION = 15
DEFAULT_DELAY = 1

parser = Lark(r"""
%import common.WS
%ignore WS
%import common.INT

duration.2: "for" INT //the numbers are priority. when there's ambiguity - which there is - assume duration first.
	| INT
delay.1: "in" INT
	| INT
sprint: duration delay
	| delay duration
	| duration
	| delay
	| //blank means use defaults
""", start='sprint')

activeSprints = {}

class SprintTransformer(Transformer):
	def sprint(self, num):
		return dict(ChainMap({}, *num))
	def duration(self, num):
		return {'duration': int(num[0])}
	def delay(self, num):
		return {'delay': int(num[0])}

window = datetime.timedelta(minutes=5)

async def send_message(client, channel, msg):
	await client.send_message(channel, msg.format(mentions=', '.join(activeSprints[channel.id]['members'].keys())))

async def make_sprint(argstring, client, channel, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	if argstring:
		sprint = SprintTransformer().transform(parser.parse(argstring))
	else:
		sprint = {}
	if 'duration' not in sprint:
		sprint['duration'] = DEFAULT_DURATION
	if 'delay' not in sprint:
		sprint['delay'] = DEFAULT_DELAY
	start_time = datetime.datetime.now() + datetime.timedelta(minutes=sprint['delay'])
	end_time = start_time + datetime.timedelta(minutes=sprint['duration'])
	activeSprints[channel.id] = {'start': start_time, 'end': end_time, 'members': {}}
	await delay_function(start_time, send_message, (client, channel, 'Starting a ' + str(sprint['duration']) + '-minute sprint with {mentions}!'))
	await delay_function(end_time, send_message, (client, channel, 'Sprint has ended, {mentions}, you have 1 minute to submit your final word counts!'))
	await delay_function(end_time + datetime.timedelta(minutes=1), end_sprint, (channel, client))
	return '{0}-minute sprint starting in {1} minutes.'.format(sprint['duration'], sprint['delay'])

async def join_sprint(user, channel, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	try:
		words = int(argstring)
	except (ValueError, TypeError):
		words = 0
	if channel.id in activeSprints:
		activeSprints[channel.id]['members'][user.mention] = {'startCount': words, 'endCount': words}
		return 'Added {0} to {1:.0f}-minute sprint starting in {2:.1f} minutes.'.format(user.mention, *describe_sprint(channel))
	else:
		return 'No active sprint.'

async def record_words(user, channel, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	try:
		words = int(argstring)
	except (ValueError, TypeError):
		words = 0
	if channel.id in activeSprints:
		activeSprints[channel.id]['members'][user.mention]['endCount'] = words
		return 'Word count for {0} updated to {1}'.format(user.mention, words)
	else:
		return 'No active sprints.'

async def end_sprint(channel, client):
	result = activeSprints.pop(channel.id)
	leaderboardString = '\n'.join('{0}: {1}'.format(*a) for a in sorted([(key, value['endCount'] - value['startCount']) for key, value in result['members'].items()], key=lambda x: x[1], reverse=true))
	await send_message(client, channel, leaderboardString)
	with BotDB(dbname, botName) as db:
		db['::'.join([channel.id, result['start'].isoformat])] = result

def describe_sprint(channel):
	if channel.id in activeSprints:
		duration = (activeSprints[channel.id]['end'] - activeSprints[channel.id]['start'])/datetime.timedelta(minutes=1)
		delay = (activeSprints[channel.id]['start'] - datetime.datetime.now())/datetime.timedelta(minutes=1)
		return duration, delay

async def delay_function(when_time, function, params):
	delay = when_time.timestamp() - datetime.datetime.now().timestamp()
	loop = asyncio.get_event_loop()
	loop.call_later(delay, lambda: loop.create_task(function(*params)))

def readme(**kwargs):
	return '''Writing Sprints:
* `!makesprint`: Creates a sprint in the current channel. Defaults to a {duration}-minute sprint starting {delay} minute(s) after the command is received. These values can be overridden:
> `!makesprint for 30` or `makesprint 30`: 30-minute sprint starting in {delay} minute(s).
> `!makesprint in 10` or `makesprint {duration} 10`: {duration}-minute sprint starting in 10 minutes.
> `!makesprint for 30 in 10` or `makesprint 30 10`: 30-minute sprint starting in 10 minutes.
* `!joinsprint`: Joins an existing sprint in this channel. Note that you must join your own sprint.
> Optionally takes a number, indicating your starting word count. e.g. `!joinsprint 253`. This is subtracted from your final word count.
* `!sprintwords x`: x is a number. Declares your final word count.
> note that both joinsprint and sprintwords can be called as many times as you like per sprint, with only the last value being saved.
'''.format(duration=DEFAULT_DURATION, delay=DEFAULT_DELAY)
