import random
import os
import logging
import yaml
import colorgen
import configmanager
log = logging.getLogger('LongSphix.Wands')
filename = 'wands.yaml'

conf = configmanager.ConfigManager(filename)

def generate_wand():
	conf.update_config()
	wood = random.choice(conf.config['woods'])
	core = random.choice(conf.config['cores'])
	length = '{0} and {1} inches'.format(random.choice(conf.config['length int']), random.choice(conf.config['length fraction']))
	flexibility = random.choice(conf.config['flexibility'])
	effect = random.choice(conf.config['effects']).format(colorgen.generate_color())

	msg = 'The wandmaker hands you a {0} {1} wand, {2} with a {3} core. {4}'.format(flexibility, wood, length, core, effect)
	return msg
