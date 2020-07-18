import datetime
import discord
import logging
log = logging.getLogger('LongSphinx.Rep')

from botdb import BotDB

DBNAME = 'rep'
POOL_MAX= 5

class Rep:
	def __init__(self):
		self.received = 0
		self.pool = POOL_MAX
		self.lastUpdatedDay = datetime.date.today() #Using date instead of time because reset at midnight

	def getPool(self):
		self.pool += (datetime.date.today() - self.lastUpdatedDay).days
		self.lastUpdatedDay = datetime.date.today()
		if self.pool > POOL_MAX:
			self.pool = POOL_MAX
		return self.pool

	def spendPool(self):
		self.getPool()
		self.pool -= 1

# Database structure: Username: (rep received, rep to give, lastUpdated)
async def rep(user, mentionTarget, argstring, server, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	if argstring and argstring.startswith('pool'):
		return poolCheck(user)
	elif argstring and argstring.startswith('lead'):
		return await leaderboard(server, **kwargs)
	elif (argstring and argstring.startswith('check')) or user == mentionTarget:
		return repCheck(mentionTarget)
	else:
		return giveRep(user, mentionTarget)

async def leaderboard(server, **kwargs):
	embed = discord.Embed()
	embed.description = '\n'.join([f'{rank}: {details[0]} ({details[1]} points)' for rank, details in enumerate(leaderlist(server), start=1)])
	return "Current Leaderboard:", embed

def giveRep(user, target):
	giver = loadUser(user)
	if giver.getPool() > 0:
		giver.spendPool()
		receiver = loadUser(target)
		receiver.received += 1
		saveUser(giver, user)
		saveUser(receiver, target)
		return '{0}, you gave a rep to {1}!'.format(user.mention, target.mention)
	return 'Sorry {0}, you have no rep to give!'.format(user.mention)

def repCheck(user):
	repInfo = loadUser(user)
	return '{0} has received {1} rep!'.format(user.mention, repInfo.received)

def poolCheck(user): 
	repInfo = loadUser(user)
	return '{0} has {1} rep points available to give.'.format(user.mention, repInfo.getPool())

def leaderlist(server):
	with BotDB(botName, DBNAME) as db:
		list = [(member.name, db[member.id].received) for member in server.members if member.id in db and db[member.id].received > 0]
		list.sort(key=lambda user: user[1], reverse=True)
		log.error(list)
		return list

def loadUser(user):
	with BotDB(botName, DBNAME) as db:
		if str(user.id) in db:
			repInfo = db[str(user.id)]
		else:
			repInfo = Rep()
	return repInfo

def saveUser(repInfo, user):
	with BotDB(botName, DBNAME) as db:
		db[str(user.id)] = repInfo

def readme(argstring, **kwargs):
	return """Rep:
* `!{0} @user` Give a rep point to another user.
* `!{0} check` Check the amount of rep you've received. @mention another user to see theirs.
* `!{0} pool` Check how much rep you have available to give.
* `!{0} lead` View rep leaderboard. Only shows members of this server, but rep earned is maintained across servers.
""".format(argstring)
