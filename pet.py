import datetime
food = 0
happy = 0
lastCheck = datetime.datetime.now()
tick = datetime.timedelta(minutes=40)

maxFood = 30
maxHappy = 30

foodGain = 6
happyGain = 3
def feed():
	global food
	update()
	if (food < maxFood):
		food = min(maxFood, food + foodGain)
		return 'You offer the wizard\'s familiar a treat from your pocket. She takes it and retreats to her perch.' + render()
	return 'You offer the wizard\'s familiar a treat from your pocket, but she seems full.' + render()

def pet():
	global happy
	update()
	happy = min(maxHappy, happy + happyGain)
	return 'You scratch the wizard\'s familiar under the chin. She chitters happily.\n' + render()

def render():
	global food
	global happy
	return '```\nFamiliar:\n Fed:\n[' + ('-'*food) + (' '*(maxFood-food)) + ']\n Happiness:\n[' + ('-'*happy) + (' '*(maxHappy-happy)) + ']\n```'

def update():
	global lastCheck
	global food
	global happy
	temp = lastCheck + tick
	if temp < datetime.datetime.now():
		lastCheck = datetime.datetime.now()
	while temp < datetime.datetime.now():
		temp += tick
		food = max(0, food - 1)
		happy = max(0, food - 1)