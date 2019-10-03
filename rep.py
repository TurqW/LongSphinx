import shelve
import datetime
import logging
log = logging.getLogger('LongSphinx.Rep')

DBNAME = 'data/rep'
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
async def rep(user, mentionTarget, input, **kwargs):
	if input and input.startswith('pool'):
		return poolCheck(user)
	elif (input and input.startswith('check')) or user == mentionTarget:
		return repCheck(mentionTarget)
	elif user != mentionTarget:
		return giveRep(user, mentionTarget)

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

def loadUser(user):
	with shelve.open(DBNAME) as db:
		if user.id in db:
			repInfo = db[user.id]
		else:
			repInfo = Rep()
	return repInfo

def saveUser(repInfo, user):
	with shelve.open(DBNAME) as db:
		db[user.id] = repInfo

def readme(**kwargs):
	return """Rep:
* `!rep @user` Give a rep point to another user.
* `!rep check` Check the amount of rep you've received. @mention another user to see theirs.
* `!rep pool` Check how much rep you have available to give.
"""
