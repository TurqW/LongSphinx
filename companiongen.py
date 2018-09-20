import random
import os
import logging
import yaml
import colorgen
import configmanager
log = logging.getLogger('LongSphix.Companions')
filename = 'companion.yaml'

conf = configmanager.ConfigManager(filename)

def generate_companion():
	conf.update_config()
	effect_color = colorgen.generate_color()
	modifier = random.choice(conf.config['modifier'])
	color = colorgen.generate_color()
	creature = random.choice(conf.config['creature'])
	ability = random.choice(conf.config['ability'])

	msg = 'As you complete the summoning spell, there is a burst of {0} smoke. Once it clears, you see a {1} {2} {3} with the ability to {4}.'.format(effect_color, color, modifier, creature, ability)
	return msg

