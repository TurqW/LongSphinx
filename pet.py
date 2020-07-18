import datetime
import discord
import random
import sys

import generator
import utils
from botdb import BotDB

tick = datetime.timedelta(minutes=120)

maxFood = 30
maxHappy = 30

foodGain = 6
happyGain = 6

dbname = 'pets'

class Pet:
	def __init__(self):
		self.food = 0
		self.happy = 0
		self.feedText = 'You offer the wizard\'s familiar a treat from your pocket. She takes it and retreats to her perch.'
		self.fullText = 'You offer the wizard\'s familiar a treat from your pocket, but she seems full.'
		self.hungryPetText = 'You try to pet the wizard\'s familiar. She tries to bite your hand. Perhaps she\'s hungry?'
		self.midPetText = 'You scratch the wizard\'s familiar under the chin. She chitters contentedly.'
		self.fullPetText = 'The wizard\'s familiar rubs against you, trilling happily.'
		self.lastCheck = datetime.datetime.now()

	def feed(self):
		self.update()
		if (self.food < maxFood):
			self.food = min(maxFood, self.food + foodGain)
			return (self.feedText, self.render())
		return (self.fullText, self.render())

	def pet(self):
		self.update()
		factor = self.food/maxFood
		message = ''
		if factor < 0.3:
			message = self.hungryPetText
		elif factor < 0.75:
			message = self.midPetText
		else:
			message = self.fullPetText
		self.happy = min(maxHappy, int(self.happy + (happyGain * factor)))
		return (message, self.render())

	def render(self):
		embed = discord.Embed()
		try:
			embed.title = self.name
			embed.description = f"{generator.extract_text(self.desc['description'])} that can {generator.extract_text(self.desc['ability'])}"
		except AttributeError:
			embed.title = 'Familiar'
		embed.add_field(name='Fed', value='```\n' + utils.drawGauge(self.food, maxFood) + '\n```', inline=False)
		embed.add_field(name='Happiness', value='```\n' + utils.drawGauge(self.happy, maxHappy) + '\n```', inline=False)
		if '.hex' in self.desc['description']['beastColor']:
			embed.color = self.desc['description']['beastColor']['.hex']
		return embed

	def update(self):
		temp = self.lastCheck + tick
		if temp < datetime.datetime.now():
			self.lastCheck = datetime.datetime.now()
		while temp < datetime.datetime.now():
			temp += tick
			self.food = max(0, self.food - 1)
			self.happy = max(0, self.food - 1)

	def setStats(self, name, desc, seed):
		self.name = name
		self.desc = desc
		self.feedText = f'You offer {name} a treat from your pocket. It seems to enjoy it.'
		self.fullText = f'You offer {name} a treat from your pocket, but it seems full.'
		self.hungryPetText = f'You try to pet {name}. It tries to bite your hand. Perhaps it\'s hungry?'
		self.midPetText = f'You scratch {name} under the chin. It looks at you contentedly.'
		self.fullPetText = f"{name} rubs against you, {desc['description']['species']['sound']['text']} happily."
		self.seed = seed


def loadPet(name):
	with BotDB(dbname, botName) as db:
		myPet = db[name]
	return myPet

def savePet(myPet, name):
	with BotDB(dbname, botName) as db:
		db[name] = myPet

async def feed(user, mentionTarget, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	if mentionTarget is not None:
		id = str(mentionTarget.id)
	else:
		id = str(user.id)
	try:
		myPet = loadPet(id)
	except:
		myPet = loadPet('0')
	message = myPet.feed()
	savePet(myPet, id)
	return message

async def pet(user, mentionTarget, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	if mentionTarget is not None:
		id = str(mentionTarget.id)
	else:
		id = str(user.id)
	try:
		myPet = loadPet(id)
	except:
		myPet = loadPet('0')
	message = myPet.pet()
	savePet(myPet, id)
	return message

async def getSeed(user, mentionTarget, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	if mentionTarget is not None:
		id = str(mentionTarget.id)
	else:
		id = str(user.id)
	try:
		myPet = loadPet(id)
	except:
		myPet = loadPet('0')
	if myPet.seed:
		return f'{myPet.name} has seed {myPet.seed}'
	else:
		return 'Seed unknown for your pet.'

async def summon(user, argstring, conf, **kwargs):
	global botName
	botName = conf.bot_name()
	id = str(user.id)
	if not argstring:
		argstring = str(random.randrange(sys.maxsize))
	myPet = Pet()
	summon = generator.generate('beast', argstring)
	myPet.setStats(generator.generate('mc.name', argstring)['text'], summon['core'], argstring)
	message = generator.extract_text(summon) + f' Its name is {myPet.name}.'
	savePet(myPet, id)
	return message

def readme(**kwargs):
	return """Pets:
* `!summon` generate a new random pet for you! **Warning: will delete your old pet if you have one.**
* `!feed` feed your pet. @mention someone else to feed their pet instead.
* `!pet` give your pet a pat. @mention someone else to pat their pet instead.
* `!getseed` find the seed for your pet. If you save this somewhere, you can `!summon <seed>` to get back to this pet if something happens.
"""
