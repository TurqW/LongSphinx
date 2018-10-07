import asyncio

async def send_message(client, channel, msg):
	await client.send_message(channel, msg)

def create_reminder(delay, client, channel, msg):
	loop = asyncio.get_event_loop()
	loop.call_later(delay, lambda: loop.create_task(send_message(client, channel, msg)))
