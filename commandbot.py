import discord
import logging
import sys

import botconfig as conf
import utils
from cogs.role_manager import RoleManager
import test

utils.check_path('logs')

if len(sys.argv) > 1:
	botname = sys.argv[1]

conf.__init__('config.yaml', botname)

logging.basicConfig(
	filename=f'logs/{botname}.log',
	format='%(asctime)s %(levelname)-8s %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
log = logging.getLogger('LongSphinx')

tokenfilename = f'{botname}.token'
	
with open(tokenfilename, 'r') as tokenfile:
	TOKEN = tokenfile.readline().strip()

is_reminder_set = False

bot = discord.Bot()

bot.add_cog(RoleManager(bot, conf))

bot.run(TOKEN)