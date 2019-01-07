import datetime
import shelve

import generator
import utils

utils.check_path('data')

tick = datetime.timedelta(minutes=120)

maxFood = 30
maxHappy = 30

foodGain = 6
happyGain = 6

dbname = 'data/pets'

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
			return self.feedText + self.render()
		return self.fullText + self.render()

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
		return message + '\n' + self.render()

	def render(self):
		try:
			about = '{name}, {description}\nAbility: {ability}'.format(
				name = self.name,
				description=generator.extract_text(self.desc['description']),
				ability=generator.extract_text(self.desc['ability']))
		except AttributeError:
			about = 'Familiar'
		return '```\n' + about + '\n Fed:\n' + utils.drawGauge(self.food, maxFood) + '\n Happiness:\n' + utils.drawGauge(self.happy, maxHappy) + '\n```'

	def update(self):
		temp = self.lastCheck + tick
		if temp < datetime.datetime.now():
			self.lastCheck = datetime.datetime.now()
		while temp < datetime.datetime.now():
			temp += tick
			self.food = max(0, self.food - 1)
			self.happy = max(0, self.food - 1)

	def setStats(self, name, desc):
		self.name = name
		self.desc = desc
		self.feedText = 'You offer {} a treat from your pocket. It seems to enjoy it.'.format(name)
		self.fullText = 'You offer {} a treat from your pocket, but it seems full.'.format(name)
		self.hungryPetText = 'You try to pet {}. It tries to bite your hand. Perhaps it\'s hungry?'.format(name)
		self.midPetText = 'You scratch {} under the chin. It looks at you contentedly.'.format(name)
		self.fullPetText = '{} rubs against you, {} happily.'.format(name, desc['description']['species']['sound']['text'])


def loadPet(name):
	with shelve.open(dbname) as db:
		myPet = db[name]
	return myPet

def savePet(myPet, name):
	with shelve.open(dbname) as db:
		db[name] = myPet

def feed(id = '0'):
	try:
		myPet = loadPet(id)
	except:
		myPet = loadPet('0')
	message = myPet.feed()
	savePet(myPet, id)
	return message

def pet(id = '0'):
	try:
		myPet = loadPet(id)
	except:
		myPet = loadPet('0')
	message = myPet.pet()
	savePet(myPet, id)
	return message

def summon(id):
	myPet = Pet()
	summon = generator.generate('beast')
	myPet.setStats(generator.generate('mc.name')['text'], summon['core'])
	message = generator.extract_text(summon) + ' Its name is {}.'.format(myPet.name)
	savePet(myPet, id)
	return message

def readme():
	return """Pets:
* `!summon` generate a new random pet for you! **Warning: will delete your old pet if you have one.**
* `!feed` feed your pet. @mention someone else to feed their pet instead.
* `!pet` give your pet a pat. @mention someone else to pat their pet instead.
"""
try:
	loadPet('0')
except:
	savePet(Pet(), '0')