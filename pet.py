import datetime
import shelve
import utils

utils.check_path("data")

tick = datetime.timedelta(minutes=40)

maxFood = 30
maxHappy = 30

foodGain = 6
happyGain = 6

dbname = 'data/pets'

class Pet:
	def __init__(self):
		self.food = 0
		self.happy = 0
		self.lastCheck = datetime.datetime.now()

	def feed(self):
		self.update()
		if (self.food < maxFood):
			self.food = min(maxFood, self.food + foodGain)
			return 'You offer the wizard\'s familiar a treat from your pocket. She takes it and retreats to her perch.' + self.render()
		return 'You offer the wizard\'s familiar a treat from your pocket, but she seems full.' + self.render()

	def pet(self):
		self.update()
		factor = self.food/maxFood
		message = ''
		if factor < 0.3:
			message = 'You try to pet the wizard\'s familiar. She tries to bite your hand. Perhaps she\'s hungry?'
		elif factor < 0.75:
			message = 'You scratch the wizard\'s familiar under the chin. She chitters contentedly.'
		else:
			message = 'The wizard\'s familiar rubs against you, trilling happily.'
		self.happy = min(maxHappy, int(self.happy + (happyGain * factor)))
		return message + '\n' + self.render()

	def render(self):
		return '```\nFamiliar:\n Fed:\n' + utils.drawGauge(self.food, maxFood) + '\n Happiness:\n' + utils.drawGauge(self.happy, maxHappy) + '\n```'

	def update(self):
		temp = self.lastCheck + tick
		if temp < datetime.datetime.now():
			self.lastCheck = datetime.datetime.now()
		while temp < datetime.datetime.now():
			temp += tick
			self.food = max(0, self.food - 1)
			self.happy = max(0, self.food - 1)

with shelve.open(dbname) as db:
	if 'mainPet' in db:
		myPet = db['mainPet']
	else:
		myPet = Pet()

def feed():
	message = myPet.feed()
	with shelve.open(dbname) as db:
		db['mainPet'] = myPet
	return message

def pet():
	message = myPet.pet()
	with shelve.open(dbname) as db:
		db['mainPet'] = myPet
	return message