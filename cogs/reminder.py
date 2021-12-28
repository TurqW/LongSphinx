import asyncio
import dateparser
import datetime
import math
import logging

from discord import Cog, Option, SlashCommandGroup, SelectOption, Interaction, Button, ButtonStyle
from discord.ui import Select, View, button
from metomi.isodatetime.parsers import TimeRecurrenceParser
from metomi.isodatetime.data import Duration, get_timepoint_for_now

import utils
from botdb import BotDB
import botconfig as conf

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
            return []


def save_reminders(schedule):
    with BotDB(conf.bot_name(), DB_NAME) as db:
        db[DB_KEY] = schedule


def save_one_reminder(channel, when_time, msg):
    schedule = load_reminders()
    schedule.append((channel.id, when_time, msg))
    save_reminders(schedule)


def delete_reminder(reminder):
    schedule = load_reminders()
    if reminder in schedule:
        schedule.remove(reminder)
        save_reminders(schedule)


async def set_all_saved_reminders(bot):
    for reminder in load_reminders():
        if reminder[1] and reminder[1] > datetime.datetime.utcnow():
            user = bot.get_user(reminder[0])
            channel = user.dm_channel
            if channel is None:
                channel = await user.create_dm()
            await set_reminder(reminder[1], channel, reminder[2])
        else:
            delete_reminder(reminder)


async def send_message(channel, msg, time):
    if (time - window) <= datetime.datetime.utcnow() <= (
            time + window):  # extra check to avoid random mistimed messages
        await channel.send(msg)
    else:
        log.error('Mistimed reminder.')
    delete_reminder((channel, time, msg))


def parse_time(time):
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


async def set_reminder(when_time, channel, msg):
    if when_time > datetime.datetime.utcnow():
        delay = when_time.timestamp() - datetime.datetime.utcnow().timestamp()
        loop = asyncio.get_running_loop()
        handle = loop.call_later(delay, lambda: loop.create_task(send_message(channel, msg, when_time)))
        scheduled_tasks[(channel.id, when_time, msg)] = handle
    else:
        log.warning('Ignoring scheduled event in the past: ' + str(when_time))


def friendly_until_string(when):
    # This is much too dense, I know. Starting from the inside:
    # Subtract now from when to get a duration
    # Convert duration to string, it looks like `10 days, 4:55:21.2435`
    # Split at the '.' and take the first part, to strip off the partial seconds
    # Split on ':' for `['10 days, 4', '55', '21']`
    # Unpack that list into the arguments for format, resulting in `10 days, 4h, 55m, 21s`
    # Replace ' days' with 'd' to get `10d, 4h, 55m, 21s`
    # Now as long as I always remember to keep this comment up to date - ok, yeah, not likely
    return '{0}h, {1}m, {2}s'.format(
        *str(when - datetime.datetime.utcnow()).split('.')[0].split(':')
    ).replace(' days', 'd')


def get_first_after(recurrence, timepoint):
    """Returns the first valid scheduled recurrence after the given timepoint, or None."""
    if timepoint < recurrence.start_point:
        return recurrence.start_point
    if timepoint is None:
        return None
    if recurrence.start_point is not None:
        iterations, seconds_since = duration_divmod(timepoint - recurrence.start_point, recurrence.duration)
        log.error('iterations: ' + str(iterations) + ' and seconds: ' + str(seconds_since))
        if not recurrence.repetitions or recurrence.repetitions > iterations:
            return timepoint + (recurrence.duration - Duration(seconds=math.floor(seconds_since)))
    '''else: # going in reverse
        candidate = None
        for next_timepoint in recurrence:
            if next_timepoint < timepoint:
                return candidate
            candidate = next_timepoint
        # when loop is done, this is the first overall timepoint (chronologically)
        return candidate'''


def duration_divmod(duration, divisor):
    return divmod(duration.get_seconds(), divisor.get_seconds())


async def set_recurring_message(recur_string, channel, msg):
    recurrence = TimeRecurrenceParser().parse(recur_string)
    now = get_timepoint_for_now()
    when_time = get_first_after(recurrence, now)
    if when_time is not None:
        delay = float(when_time.get("seconds_since_unix_epoch")) - datetime.datetime.now().timestamp()
        loop = asyncio.get_event_loop()
        loop.call_later(delay, lambda: loop.create_task(send_recurring_message(recur_string, channel, msg)))


async def send_recurring_message(recur_string, channel, msg):
    await channel.send(msg)
    await set_recurring_message(recur_string, channel, msg)


def get_reminder_by_user_and_content(user_id, msg):
    return next((x for x in load_reminders() if x[0] == user_id and x[2].replace("Reminder: ", "") == msg), None)


def reminder_list_message(user_id):
    all_reminders = load_reminders()
    all_reminders.sort(key=lambda x: x[1])
    string_list = [f'{friendly_until_string(when)}: {msg.replace("Reminder: ", "")}' for (channel, when, msg) in
                   all_reminders if channel == user_id]
    if string_list:
        return '\n'.join(string_list)
    else:
        return NO_REMINDERS_MESSAGE


class DeleteReminderView(View):
    def __init__(self):
        super().__init__()
        self.dropdown = None

    @button(label="Delete some reminders?", row=2, style=ButtonStyle.grey, emoji='🗑️')
    async def delete(self, this_button: Button, interaction: Interaction):
        if not self.dropdown:
            options = [SelectOption(label=reminder[2].replace("Reminder: ", "")) for reminder in load_reminders() if
                       reminder[0] == interaction.user.id]

            self.dropdown = Select(
                placeholder="Delete which reminder?",
                max_values=len(options),
                options=options
            )
            self.add_item(self.dropdown)

            this_button.label = 'Delete'
            this_button.style = ButtonStyle.red
            await interaction.response.edit_message(view=self)
        else:
            for reminder in self.dropdown.values:
                reminder_tuple = get_reminder_by_user_and_content(interaction.user.id, reminder)
                if reminder_tuple:
                    delete_reminder(reminder_tuple)
                    if reminder_tuple in scheduled_tasks:
                        scheduled_tasks[reminder_tuple].cancel()
                        del scheduled_tasks[reminder_tuple]
            msg = reminder_list_message(interaction.user.id)
            await interaction.response.edit_message(
                content=msg,
                view=DeleteReminderView() if msg != NO_REMINDERS_MESSAGE else None
            )


class Reminders(Cog):
    def __init__(self, bot):
        self.bot = bot

    reminderGroup = SlashCommandGroup('remind', 'Set and manage reminders.')

    @reminderGroup.command(name='set', description='Schedule a reminder DM.')
    async def message_reminder(
            self, ctx,
            content: Option(str, 'What should I remind you about?'),
            time: Option(str, 'A time and/or date in UTC, or start with "in" to schedule a specific duration from now.')
    ):
        when_time = parse_time(time)
        if not when_time:
            await ctx.respond(f'Unable to parse time string: ' + time, ephemeral=True)
            return
        msg = f'Reminder: {content}'
        save_one_reminder(ctx.user, when_time, msg)
        await set_reminder(when_time, ctx.user, msg)
        await ctx.respond(f'I\'ll DM you "{msg}" in {friendly_until_string(when_time)}.', ephemeral=True)

    @reminderGroup.command(name='list', description='View all your reminders')
    async def list_my_reminders(self, ctx):
        msg = reminder_list_message(ctx.user.id)
        if msg != NO_REMINDERS_MESSAGE:
            await ctx.respond(msg, view=DeleteReminderView(), ephemeral=True)
        else:
            await ctx.respond(msg, ephemeral=True)

    @Cog.listener()
    async def on_ready(self):
        global is_reminder_set
        log.debug(f'Re-initializing reminders...')
        if not is_reminder_set:
            for server in self.bot.guilds:
                recurring = conf.get_object(server, 'recurring')
                if recurring:
                    for event in recurring:
                        channel = utils.find_channel(event['channel'], server)
                        msg = event['message']
                        await set_recurring_message(event['time'], channel, msg)
            await set_all_saved_reminders(self.bot)
        is_reminder_set = True
        log.debug(f'Reminders re-initialized')
