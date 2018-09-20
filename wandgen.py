import random
import os
import logging
import yaml
log = logging.getLogger('LongSphix.Wands')
filename = 'wands.yaml'
lastmod = os.stat(filename).st_mtime

with open(filename, 'r') as stream:
	try:
		config = yaml.load(stream)
	except yaml.YAMLError as exc:
		sys.exit()

def generate_wand():
	update_config()
	wood = random.choice(config['woods'])
	core = random.choice(config['cores'])
	length = '{0} and {1} inches'.format(random.choice(config['length int']), random.choice(config['length fraction']))
	flexibility = random.choice(config['flexibility'])
	effect = random.choice(config['effects']).format(random.choice(config['colors']))

	msg = 'The wandmaker hands you a {0} {1} wand, {2} with a {3} core. {4}'.format(flexibility, wood, length, core, effect)
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
