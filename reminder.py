import asyncio
import dateparser
import datetime

active_reminders = []

async def send_message(client, channel, msg):
	await client.send_message(channel, msg)

async def message_reminder(when, client, channel, msg):
	when_time = dateparser.parse(when)
	await client.send_message(channel, 'Reminder set for {0}, current time is {1}'.format(when_time.isoformat(), datetime.datetime.now().isoformat()))
	await set_reminder(when_time, client, channel, msg)

async def set_reminder(when_time, client, channel, msg):
	delay = when_time.timestamp() - datetime.datetime.now().timestamp()
	loop = asyncio.get_event_loop()
	loop.call_later(delay, lambda: loop.create_task(send_message(client, channel, msg)))
