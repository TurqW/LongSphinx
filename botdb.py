import shelve
import utils

DBLOCATION='data/{0}/{1}'

# intended to be basically a drop-in wrapper for shelve, allowing for a little
# bit of custom logic such as redirecting to bot-name-specific folders

class BotDB(object):
	def __init__(self, botName, dbName):
		self.botName = botName
		self.dbName = dbName
		utils.check_path(f'data/{self.botName}')

	def __enter__(self):
		self.db = shelve.open(DBLOCATION.format(self.botName, self.dbName))
		return self.db

	def __exit__(self, *args):
		self.db.close()
