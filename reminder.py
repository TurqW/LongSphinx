import asyncio
import dateparser
import datetime
import logging
import isodatetime.parsers as dtparse
import isodatetime.data as dtdata

log = logging.getLogger('LongSphinx.Reminder')

active_reminders = []
window = datetime.timedelta(minutes=5)

async def send_message(client, channel, msg, time):
	if (time - window) <= datetime.datetime.now() <= (time + window): #extra check to avoid random mistimed messages
		await client.send_message(channel, msg)
	else:
		log.error('Mistimed reminder.')

async def message_reminder(input, client, channel, **kwargs):
	when_time = dateparser.parse(input)
	msg = 'reminder: {0}'.format(input)
	await set_reminder(when_time, client, channel, msg)
	return 'Reminder set for {0}, current time is {1}'.format(when_time.isoformat(), datetime.datetime.now().isoformat())

async def set_reminder(when_time, client, channel, msg):
	if when_time > datetime.datetime.now():
		delay = when_time.timestamp() - datetime.datetime.now().timestamp()
		loop = asyncio.get_event_loop()
		loop.call_later(delay, lambda: loop.create_task(send_message(client, channel, msg, when_time)))
	else:
		log.warning('Ignoring scheduled event in the past: ' + str(when_time))

def get_first_after(recurrence, timepoint):
    """Returns the first valid scheduled recurrence after the given timepoint, or None."""
    if timepoint is None:
        return None
    if recurrence.start_point is not None:
        for candidate in recurrence:
            if candidate > timepoint:
                return candidate
        return None
    else: # going in reverse
        candidate = None
        for next_timepoint in recurrence:
            if next_timepoint < timepoint:
                return candidate
            candidate = next_timepoint
        # when loop is done, this is the first overall timepoint (chronologicaly)
        return candidate

async def send_recurring_message(recur_string, client, channel, msg):
	recurrence = dtparse.TimeRecurrenceParser().parse(recur_string)
	now = dtdata.get_timepoint_for_now()
	when_time = get_first_after(recurrence, now)
	await client.send_message(channel, msg)
	if when_time is not None:
		delay = float(when_time.get("seconds_since_unix_epoch")) - datetime.datetime.now().timestamp()
		loop = asyncio.get_event_loop()
		loop.call_later(delay, lambda: loop.create_task(send_recurring_message(recur_string, client, channel, msg)))

def readme(**kwargs):
	return 'Still under development.'
