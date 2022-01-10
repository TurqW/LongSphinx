import asyncio
from math import floor

import dateparser
import datetime
import logging

from discord import Cog, Option, SlashCommandGroup, SelectOption, Interaction
from discord.ui import View
from metomi.isodatetime.parsers import TimeRecurrenceParser
from metomi.isodatetime.data import get_timepoint_for_now, Duration
from uuid import uuid4
from w2n import numwords_in_sentence

from discordclasses.utils import time_delta_to_parts, find_channel, grammatical_number, round_time_dict_to_minutes
from discordclasses.deletable import DeletableListView
from persistence.botdb import BotDB
from persistence import botconfig as conf

log = logging.getLogger('LongSphinx.Reminder')
is_reminder_set = False

DB_NAME = 'schedule'
DB_KEY = '0'
NO_REMINDERS_MESSAGE = 'No reminders set. You can make new ones with `/remind set`.'
window = datetime.timedelta(minutes=5)

scheduled_tasks = {}


def load_reminders():
    with BotDB(conf.bot_name(), DB_NAME) as db:
        if DB_KEY in db:
            return db[DB_KEY]
        else:
            return {}


def save_reminders(schedule):
    with BotDB(conf.bot_name(), DB_NAME) as db:
        db[DB_KEY] = schedule


def save_one_reminder(channel, when_time, msg):
    schedule = load_reminders()
    reminder_id = str(uuid4())
    schedule[reminder_id] = (channel.id, when_time, msg)
    save_reminders(schedule)
    return reminder_id


def delete_reminder(reminder_id):
    schedule = load_reminders()
    if reminder_id in schedule:
        schedule.pop(reminder_id)
        save_reminders(schedule)


async def set_all_saved_reminders(bot):
    for reminder_id, reminder in load_reminders().items():
        if reminder[1] and reminder[1] > datetime.datetime.utcnow():
            user = bot.get_user(reminder[0])
            channel = user.dm_channel
            if channel is None:
                channel = await user.create_dm()
            await set_reminder(reminder_id, reminder[1], channel, reminder[2])
        else:
            delete_reminder(reminder)


async def send_message(reminder_id, channel, msg, time):
    if (time - window) <= datetime.datetime.utcnow() <= (
            time + window):  # extra check to avoid random mistimed messages
        await channel.send(msg)
    else:
        log.error('Mistimed reminder.')
    delete_reminder(reminder_id)


def parse_time(time):
    time = numwords_in_sentence(time)
    when_time = dateparser.parse(time, settings={'TIMEZONE': 'UTC'})
    if when_time < datetime.datetime.utcnow():
        # Maybe they're trolling, or maybe they didn't put "in"
        when_time = dateparser.parse('in' + time, settings={'TIMEZONE': 'UTC'})
    if not when_time or when_time < datetime.datetime.utcnow():
        # if that didn't work, just fail it.
        return None
    if when_time.tzinfo is not None:
        when_time = when_time.replace(tzinfo=None)
    return when_time


async def set_reminder(reminder_id, when_time, channel, msg):
    if when_time > datetime.datetime.utcnow():
        delay = when_time.timestamp() - datetime.datetime.utcnow().timestamp()
        loop = asyncio.get_running_loop()
        handle = loop.call_later(delay, lambda: loop.create_task(send_message(reminder_id, channel, msg, when_time)))
        scheduled_tasks[reminder_id] = handle
    else:
        log.warning('Ignoring scheduled event in the past: ' + str(when_time))


def friendly_until_string(when, with_prepositions=False):
    if when - datetime.datetime.utcnow() > datetime.timedelta(days=100):
        # If the days part would be 3 digits, show a date instead
        return ('on ' if with_prepositions else '') + \
               (when + (datetime.datetime.now() - datetime.datetime.utcnow())).strftime('%B %d, %Y')
    # The other case gets a bit weird, because there's no timedelta.format method.
    time_dict = time_delta_to_parts(when - datetime.datetime.utcnow())
    if time_dict['day'] == 0 and time_dict['hour'] == 0 and time_dict['minute'] == 0:
        # If there's nothing but seconds, show seconds
        return ('in ' if with_prepositions else '') + f'{time_dict["second"]} seconds'
    # round the minutes
    time_dict = round_time_dict_to_minutes(time_dict)
    # Filter out any 0's and ignore seconds
    friendly_strings = [f'{value} {grammatical_number(key, value)}' for (key, value) in time_dict.items()
                        if value != 0 and key != 'second']
    return ('in ' if with_prepositions else '') + ', '.join(friendly_strings)


# see https://github.com/metomi/isodatetime/pull/202
def get_next_after(recurrence, timepoint):
    if recurrence._get_is_in_bounds(timepoint):
        iterations, seconds_since = divmod((timepoint - recurrence.start_point).get_seconds(),
                                           recurrence.duration.get_seconds())
        return timepoint + (recurrence.duration - Duration(seconds=floor(seconds_since)))
    elif timepoint < recurrence.start_point:
        return recurrence.start_point
    return None


async def set_recurring_message(recur_string, channel, msg):
    recurrence = TimeRecurrenceParser().parse(recur_string)
    now = get_timepoint_for_now()
    when_time = get_next_after(recurrence, now)
    if when_time is not None:
        delay = float(when_time.get("seconds_since_unix_epoch")) - datetime.datetime.now().timestamp()
        loop = asyncio.get_event_loop()
        loop.call_later(delay, lambda: loop.create_task(send_recurring_message(recur_string, channel, msg)))


async def send_recurring_message(recur_string, channel, msg):
    await channel.send(msg)
    await set_recurring_message(recur_string, channel, msg)


def reminder_list_message(user_id):
    all_reminders = load_reminders().values()
    all_reminders = sorted(all_reminders, key=lambda x: x[1])
    string_list = [f'{friendly_until_string(when)}:\n> {msg.replace("Reminder: ", "")}' for (channel, when, msg) in
                   all_reminders if channel == user_id]
    if string_list:
        return '\n'.join(string_list)
    else:
        return NO_REMINDERS_MESSAGE


async def list_refresher(interaction: Interaction, view: View):
    msg = reminder_list_message(interaction.user.id)
    await interaction.response.edit_message(
        content=msg,
        view=view if msg != NO_REMINDERS_MESSAGE else None
    )


def delete_reminders(ids):
    """
    Used by the DeletableListView
    @param ids: list of ids to delete
    @return:
    """
    for reminder_id in ids:
        delete_reminder(reminder_id)
        if reminder_id in scheduled_tasks:
            scheduled_tasks[reminder_id].cancel()
            del scheduled_tasks[reminder_id]


def reminders_for_dropdown(interaction: Interaction):
    """
     Used by the DeletableListView
     @param interaction:
     @return: list of SelectOptions with that user's reminders
     """
    return [SelectOption(label=reminder[2].replace("Reminder: ", ""), value=key) for (key, reminder) in
            sorted(load_reminders().items(), key=lambda x: x[1][1]) if
            reminder[0] == interaction.user.id]


class Reminders(Cog):
    def __init__(self, bot):
        self.bot = bot

    reminderGroup = SlashCommandGroup('remind', 'Set and manage reminders.')

    @reminderGroup.command(name='set', description='Schedule a reminder DM.')
    async def message_reminder(
            self, ctx,
            content: Option(str, 'What should I remind you about?'),
            time: Option(str, 'A time and/or date in UTC, or a duration from now.')
    ):
        when_time = parse_time(time)
        if not when_time:
            await ctx.respond(f'Unable to parse time string: ' + time, ephemeral=True)
            return
        msg = f'Reminder: {content}'
        reminder_id = save_one_reminder(ctx.user, when_time, msg)
        await set_reminder(reminder_id, when_time, ctx.user, msg)
        await ctx.respond(f'I\'ll DM you "{msg}" {friendly_until_string(when_time, True)}.', ephemeral=True)

    @reminderGroup.command(name='list', description='View all your reminders')
    async def list_my_reminders(self, ctx):
        msg = reminder_list_message(ctx.user.id)
        view = None if msg == NO_REMINDERS_MESSAGE else DeletableListView(list_refresher, reminders_for_dropdown,
                                                                          delete_reminders)
        await ctx.respond(msg, view=view, ephemeral=True)

    @Cog.listener()
    async def on_ready(self):
        global is_reminder_set
        log.debug(f'Re-initializing reminders...')
        if not is_reminder_set:
            for server in self.bot.guilds:
                recurring = conf.get_object(server, 'recurring')
                if recurring:
                    for event in recurring:
                        channel = find_channel(event['channel'], server)
                        msg = event['message']
                        await set_recurring_message(event['time'], channel, msg)
            await set_all_saved_reminders(self.bot)
        is_reminder_set = True
        log.debug(f'Reminders re-initialized')
