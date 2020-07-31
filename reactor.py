async def autoreact(message, conf, **kwargs):
	for emoji in conf.get_object(message.guild, 'autoreact'):
		for trigger in emoji['triggers']:
			if trigger.lower() in message.content.lower():
				await message.add_reaction(emoji['emoji'])