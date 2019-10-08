import asyncio
import dateparser
import datetime
import math
import logging
import shelve
import isodatetime.parsers as dtparse
import isodatetime.data as dtdata

log = logging.getLogger('LongSphinx.Reminder')

DBNAME = 'data/schedule'
DBKEY = '0'
window = datetime.timedelta(minutes=5)

def load_reminders():
	with shelve.open(DBNAME) as db:
		if DBKEY in db:
			return db[DBKEY]
		else:
			return []

def save_reminders(schedule):
	with shelve.open(DBNAME) as db:
		db[DBKEY] = schedule

def list_all_set_channels():
	with shelve.open(DBNAME) as db:
		return list(db.keys())

def save_one_reminder(channel, when_time, msg):
	schedule = load_reminders()
	schedule.append((channel, when_time, msg))
	save_reminders(schedule)

def delete_reminder(reminder):
	schedule = load_reminders()
	schedule.remove(reminder)
	save_reminders(schedule)

async def set_all_saved_reminders(client):
	for reminder in load_reminders():
		if reminder[1] > datetime.datetime.now():
			await set_reminder(reminder[1], client, reminder[0], reminder[2])
		else:
			delete_reminder(reminder)

async def send_message(client, channel, msg, time):
	if (time - window) <= datetime.datetime.now() <= (time + window): #extra check to avoid random mistimed messages
		await client.send_message(channel, msg)
	else:
		log.error('Mistimed reminder.')

async def message_reminder(input, client, user, **kwargs):
	splitindex = input.rfind(' in ')
	when_time = dateparser.parse(input[splitindex:])
	msg = 'Reminder: {0}'.format(input[:splitindex])
	save_one_reminder(user, when_time, msg)
	await set_reminder(when_time, client, user, msg)
	return 'I\'ll send you a reminder{0}.'.format(input[splitindex:])

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
        iterations, seconds_since = dividemod(timepoint - recurrence.start_point, recurrence.duration)
        log.error('iterations: ' + str(iterations) + ' and seconds: ' + str(seconds_since))
        if not recurrence.repetitions or recurrence.repetitions > iterations:
        	return timepoint + (recurrence.duration - dtdata.Duration(seconds=math.floor(seconds_since)))
    '''else: # going in reverse
        candidate = None
        for next_timepoint in recurrence:
            if next_timepoint < timepoint:
                return candidate
            candidate = next_timepoint
        # when loop is done, this is the first overall timepoint (chronologically)
        return candidate'''

def dividemod(duration, divisor):
	return divmod(duration.get_seconds(), divisor.get_seconds())

async def set_recurring_message(recur_string, client, channel, msg):
	recurrence = dtparse.TimeRecurrenceParser().parse(recur_string)
	now = dtdata.get_timepoint_for_now()
	when_time = get_first_after(recurrence, now)
	if when_time is not None:
		delay = float(when_time.get("seconds_since_unix_epoch")) - datetime.datetime.now().timestamp()
		loop = asyncio.get_event_loop()
		loop.call_later(delay, lambda: loop.create_task(send_recurring_message(recur_string, client, channel, msg)))

async def send_recurring_message(recur_string, client, channel, msg):
	await client.send_message(channel, msg)
	await set_recurring_message(recur_string, client, channel, msg)

def readme(**kwargs):
	return 'Still under development.'
