import random
import os
import logging
import yaml
import colorgen
import configmanager
log = logging.getLogger('LongSphix.Potions')
filename = 'potions.yaml'

conf = configmanager.ConfigManager(filename)

#TODO: potion effects
#TODO: how you got the potion?
def generate_potion():
	conf.update_config()
	liquid_color = colorgen.generate_color()
	liquid_modifier = random.choice(conf.config['liquids'])
	bottle = random.choice(conf.config['bottles'])
	effect = random.choice(conf.config['effects'])

	msg = 'You find a {0} full of {1} {2} liquid. When you drink it, {3}.'.format(bottle, liquid_modifier, liquid_color, effect)
	return msg

