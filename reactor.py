import re
from datetime import datetime, timedelta

recent = {}

async def autoreact(message, conf, **kwargs):
	for emoji in conf.get_object(message.guild, 'autoreact'):
		for trigger in emoji['triggers']:
			if re.search(trigger, message.content, re.IGNORECASE) and timecheck(emoji['emoji']+str(message.channel.id)):
				recent[emoji['emoji']+str(message.channel.id)] = datetime.now()
				await message.add_reaction(emoji['emoji'])

async def autoreply(message, conf, **kwargs):
	for reply in conf.get_object(message.guild, 'autoreply'):
		for trigger in reply['triggers']:
			if re.search(trigger, message.content, re.IGNORECASE) and timecheck(reply['text']+str(message.channel.id)):
				recent[reply['text']+str(message.channel.id)] = datetime.now()
				await message.channel.send(content=reply['text'], reference=message)

def timecheck(key):
	try:
		return recent[key] < datetime.now() - timedelta(minutes=5)
	except:
		return True
