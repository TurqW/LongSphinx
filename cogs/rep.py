import datetime
import discord
from discord.commands import Option, SlashCommandGroup
import logging
from botdb import BotDB
import botconfig as conf

log = logging.getLogger('LongSphinx.Rep')

DBNAME = 'rep'
POOL_MAX = 5


class Rep:
    def __init__(self):
        self.received = 0
        self.pool = POOL_MAX
        self.lastUpdatedDay = datetime.date.today()  # Using date instead of time because reset at midnight

    def get_pool(self):
        self.pool += (datetime.date.today() - self.lastUpdatedDay).days
        self.lastUpdatedDay = datetime.date.today()
        if self.pool > POOL_MAX:
            self.pool = POOL_MAX
        return self.pool

    def spend_pool(self):
        self.get_pool()
        self.pool -= 1


def leader_list(members) -> list[(str, int)]:
    with BotDB(conf.bot_name(), DBNAME) as db:
        sorted_list = [(member.name, db[str(member.id)].received) for member in members if
                       str(member.id) in db and db[str(member.id)].received > 0]
        sorted_list.sort(key=lambda user: user[1], reverse=True)
        return sorted_list


def load_user(user):
    with BotDB(conf.bot_name(), DBNAME) as db:
        if str(user.id) in db:
            rep_info = db[str(user.id)]
        else:
            rep_info = Rep()
    return rep_info


def save_user(rep_info, user):
    with BotDB(conf.bot_name(), DBNAME) as db:
        db[str(user.id)] = rep_info


class RepCommands(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    repGroup = SlashCommandGroup('rep', 'Give out reputation points', guild_ids=[489197880809095168])

    @repGroup.command(name='lead', description='Rep leaderboards!')
    async def leaderboard(self, ctx):
        formatted = '\n'.join([f'{rank}: {details[0]} ({details[1]} points)' for rank, details in
                               enumerate(leader_list(await ctx.guild.fetch_members().flatten()), start=1)])
        embed = discord.Embed(title='Current Rep Leaderboard:', description=formatted)
        await ctx.respond('', embed=embed)

    @repGroup.command(name='give', description='Give a reputation point!')
    async def give_rep(self, ctx, target: Option(discord.Member, 'Who gets the rep?')):
        if ctx.user.id == target.id:
            return await self.rep_check(ctx, target)
        giver = load_user(ctx.user)
        if giver.get_pool() > 0:
            giver.spend_pool()
            receiver = load_user(target)
            receiver.received += 1
            save_user(giver, ctx.user)
            save_user(receiver, target)
            await ctx.respond(f'{ctx.user.mention}, you gave a rep to {target.mention}!')
        else:
            await ctx.respond(f'Sorry {ctx.user.mention}, you have no rep to give!', ephemeral=True)

    @repGroup.command(name='check', description='Check the rep a user has accumulated.')
    async def rep_check(self, ctx,
                        target: Option(discord.Member, 'Whose rep do you want to view?', required=False)):
        if target:
            user = target
        else:
            user = ctx.user
        rep_info = load_user(user)
        await ctx.respond(
            f'{user.mention} has received {rep_info.received} rep and has {rep_info.get_pool()} rep available to give!')
