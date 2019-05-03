import asyncio
import dateparser
import datetime
import logging

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
