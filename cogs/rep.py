import datetime
import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands
import logging
log = logging.getLogger('LongSphinx.Rep')

from botdb import BotDB
import botconfig as conf
import utils

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

class RepCommands(discord.Cog):
	def __init__(self, bot):
		self.bot = bot

	repGroup = SlashCommandGroup('rep', 'Give out reputation points', guild_ids=[489197880809095168])

	@repGroup.command(name='lead', description='Rep leaderboards!')
	async def leaderboard(self, ctx):
		formatted = '\n'.join([f'{rank}: {details[0]} ({details[1]} points)' for rank, details in enumerate(self.leaderlist(await ctx.guild.fetch_members().flatten()), start=1)])
		embed = discord.Embed(title='Current Rep Leaderboard:', description=formatted)
		await ctx.respond('', embed=embed)

	@repGroup.command(name='give', description='Give a reputation point!')
	async def giveRep(self, ctx, target:  Option(str, "Who gets the rep?", autocomplete=utils.user_picker)):
		target_user = ctx.guild.get_member_named(target)
		giver = self.loadUser(ctx.user)
		if giver.getPool() > 0:
			giver.spendPool()
			receiver = self.loadUser(target_user)
			receiver.received += 1
			self.saveUser(giver, ctx.user)
			self.saveUser(receiver, target_user)
			await ctx.respond(f'{ctx.user.mention}, you gave a rep to {target_user.mention}!')
		else:
			await ctx.respond(f'Sorry {ctx.user.mention}, you have no rep to give!', ephemeral=True)

	@repGroup.command(name='check', description='Check the rep a user has accumulated.')
	async def repCheck(self, ctx, target:  Option(str, "Whose rep?", autocomplete=utils.user_picker, required=False) = None):
		if target:
			user = ctx.guild.get_member_named(target)
		else:
			user = ctx.user
		repInfo = self.loadUser(user)
		await ctx.respond(f'{user.mention} has received {repInfo.received} rep and has {repInfo.getPool()} rep available to give!')

	def leaderlist(self, members):
		with BotDB(conf.bot_name(), DBNAME) as db:
			list = [(member.name, db[str(member.id)].received) for member in members if str(member.id) in db and db[str(member.id)].received > 0]
			list.sort(key=lambda user: user[1], reverse=True)
			return list

	def loadUser(self, user):
		with BotDB(conf.bot_name(), DBNAME) as db:
			if str(user.id) in db:
				repInfo = db[str(user.id)]
			else:
				repInfo = Rep()
		return repInfo

	def saveUser(self, repInfo, user):
		with BotDB(conf.bot_name(), DBNAME) as db:
			db[str(user.id)] = repInfo

def readme(argstring, **kwargs):
	return """Rep:
* `!{0} @user` Give a rep point to another user.
* `!{0} check` Check the amount of rep you've received. @mention another user to see theirs.
* `!{0} pool` Check how much rep you have available to give.
* `!{0} lead` View rep leaderboard. Only shows members of this server, but rep earned is maintained across servers.
""".format(argstring)
