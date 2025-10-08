from discord import slash_command, Cog, Option
from ics import Calendar, Event
import requests

def format_message(e: Event):
    if e.name and e.description:
        return "**" + e.name + "**\n>>> " + e.description
    return e.name if e.name else e.description

class CalCog(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='calendar', description='Load a calendar')
    async def caltest(
            self, ctx,
            url: Option(str, 'iCal URL')
    ):
        await ctx.defer(ephemeral=True)
        c = Calendar(requests.get(url).text)
        #e = list(c.timeline)[0]
        msg = [line.value for line in c.extra if line.name == "X-WR-CALNAME"][0]
        await ctx.send_followup(msg)

'''
Calendar:
X-WR-CALNAME: name

Event:
Name
Begin/End/Duration
Description
Location can be a channel

What I save:
Key: ServerID:CalendarUrl
DefaultChannelId
Name


'''