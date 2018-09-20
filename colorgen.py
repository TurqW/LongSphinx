import random
import os
import logging
import yaml
log = logging.getLogger('LongSphix.Colors')
filename = 'colors.yaml'
lastmod = os.stat(filename).st_mtime

with open(filename, 'r') as stream:
	try:
		config = yaml.load(stream)
	except yaml.YAMLError as exc:
		sys.exit()

def generate_color():
	update_config()
	return random.choice(config['colors'])

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
