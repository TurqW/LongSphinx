import asyncio
import datetime
import logging

from discord import SlashCommandGroup, Option, Interaction, Cog, ButtonStyle
from discord.ui import View, button, Button

from persistence import botconfig as conf
from persistence.botdb import BotDB

log = logging.getLogger('LongSphinx.WriteSprint')

dbname = 'sprints'
DEFAULT_DURATION = 15
DEFAULT_DELAY = 1

activeSprints = {}

window = datetime.timedelta(minutes=5)


async def send_message(channel, msg):
    await channel.send(msg.format(mentions=', '.join(activeSprints[channel.id]['members'].keys())))


async def end_sprint(channel):
    result = activeSprints.pop(channel.id)
    leaderboardString = '\n'.join('{0}: {1}'.format(*a) for a in sorted(
        [(key, value['endCount'] - value['startCount']) for key, value in result['members'].items()],
        key=lambda x: x[1], reverse=True))
    await channel.send(leaderboardString)
    with BotDB(conf.bot_name(), dbname) as db:
        db['::'.join([str(channel.id), result['start'].isoformat()])] = result


def describe_sprint(channel):
    if channel.id in activeSprints:
        duration = (activeSprints[channel.id]['end'] - activeSprints[channel.id]['start']) / datetime.timedelta(
            minutes=1)
        delay = (activeSprints[channel.id]['start'] - datetime.datetime.now()) / datetime.timedelta(minutes=1)
        return duration, delay


async def delay_function(when_time, function, params):
    delay = when_time.timestamp() - datetime.datetime.now().timestamp()
    loop = asyncio.get_event_loop()
    loop.call_later(delay, lambda: loop.create_task(function(*params)))


class NewSprintView(View):
    def __init__(self, timeout, channel):
        super().__init__(timeout=timeout)
        self.channel = channel

    @button(
        label="Join!",
        style=ButtonStyle.blurple
    )
    async def join(self, _: Button, interaction: Interaction):
        activeSprints[self.channel.id]['members'][interaction.user.mention] = {'startCount': 0, 'endCount': 0}
        await self.channel.send('Added {0} to {1:.0f}-minute sprint starting in {2:.1f} minutes.'
                                .format(interaction.user.mention, *describe_sprint(self.channel)))

    async def on_timeout(self):
        self.clear_items()
        await self.interaction.edit_original_message(view=self)


class WriteSprint(Cog):
    def __init__(self, bot):
        self.bot = bot

    sprintGroup = SlashCommandGroup('sprint', 'Create and manage writing sprints.')

    @sprintGroup.command(name='make', description='Set up a new writing sprint.')
    async def make_sprint(self, ctx,
                          delay: Option(int, 'Minutes until the sprint starts.', required=False) = DEFAULT_DELAY,
                          duration: Option(int, 'Sprint duration in minutes', required=False) = DEFAULT_DURATION):
        start_time = datetime.datetime.now() + datetime.timedelta(minutes=delay)
        end_time = start_time + datetime.timedelta(minutes=duration)
        activeSprints[ctx.channel.id] = {'start': start_time, 'end': end_time, 'members': {}}
        await delay_function(start_time, send_message,
                             (ctx.channel, 'Starting a ' + str(duration) + '-minute sprint with {mentions}!'))
        await delay_function(end_time, send_message,
                             (ctx.channel,
                              'Sprint has ended, {mentions}, you have 1 minute to submit your final word counts!'))
        await delay_function(end_time + datetime.timedelta(minutes=1), end_sprint, [ctx.channel])
        view = NewSprintView(delay * 60 + duration * 60, ctx.channel)
        view.interaction = await ctx.respond('{0}-minute sprint starting in {1} minutes.'.format(duration, delay), view=view)

    @sprintGroup.command(name='join', description='Join an existing writing sprint in this channel')
    async def join_sprint(self, ctx,
                          words: Option(int, 'Your starting wordcount. Will be subtracted from your total.',
                                        required=False) = 0):
        if ctx.channel.id in activeSprints:
            activeSprints[ctx.channel.id]['members'][ctx.user.mention] = {'startCount': words, 'endCount': words}
            await ctx.respond('Added {0} to {1:.0f}-minute sprint starting in {2:.1f} minutes.'
                              .format(ctx.user.mention, *describe_sprint(ctx.channel)))
        else:
            await ctx.respond('No active sprints.', ephemeral=True)

    @sprintGroup.command(name='submit', description='Submit your final wordcount for the sprint in this channel')
    async def submit_words(self, ctx,
                           words: Option(int, 'Your final wordcount.')):
        if ctx.channel.id in activeSprints:
            activeSprints[ctx.channel.id]['members'][ctx.user.mention]['endCount'] = words
            await ctx.respond('Word count for {0} updated to {1}'.format(ctx.user.mention, words))
        else:
            await ctx.respond('No active sprints.', ephemeral=True)
