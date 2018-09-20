import random
import os
import logging
import yaml
import colorgen
log = logging.getLogger('LongSphix.Companions')
filename = 'companion.yaml'
lastmod = os.stat(filename).st_mtime

with open(filename, 'r') as stream:
	try:
		config = yaml.load(stream)
	except yaml.YAMLError as exc:
		sys.exit()

def generate_companion():
	update_config()
	effect_color = colorgen.generate_color()
	modifier = random.choice(config['modifier'])
	color = colorgen.generate_color()
	creature = random.choice(config['creature'])
	ability = random.choice(config['ability'])

	msg = 'As you complete the summoning spell, there is a burst of {0} smoke. Once it clears, you see a {1} {2} {3} with the ability to {4}.'.format(effect_color, color, modifier, creature, ability)
	return msg

def update_config():
	global lastmod
	global config
	newlastmod = os.stat(filename).st_mtime
	if newlastmod > lastmod:
		log.info('New wand config found. Loading...')
		with open(filename, 'r') as stream:
			try:
				config = yaml.load(stream)
				lastmod = newlastmod
			except yaml.YAMLError as exc:
				log.error(exc)
				log.error('YAML invalid, sticking with version from {0}'.format(lastmod))
