import shelve

from discordclasses import utils

DB_LOCATION = 'data/{0}/{1}'


# intended to be basically a drop-in wrapper for shelve, allowing for a
# bit of custom logic such as redirecting to bot-name-specific folders

class BotDB(object):
    def __init__(self, bot_name, db_name):
        self.botName = bot_name
        self.dbName = db_name
        utils.check_path(f'data/{self.botName}')

    def __enter__(self):
        self.db = shelve.open(DB_LOCATION.format(self.botName, self.dbName))
        return self.db

    def __exit__(self, *args):
        self.db.close()
