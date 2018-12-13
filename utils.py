import os

fullGaugeChar = '='
emptyGaugeChar = ' '

def check_path(name):
	if not os.path.exists(name):
		os.makedirs(name)

def drawGauge(value, max):
	return '[' + fullGaugeChar*value + emptyGaugeChar*(max-value) + ']'
