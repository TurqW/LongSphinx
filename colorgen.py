import random
import os
import logging
import yaml
import configmanager
log = logging.getLogger('LongSphix.Colors')
filename = 'colors.yaml'

conf = configmanager.ConfigManager(filename)

def generate_color():
	conf.update_config()
	return random.choice(conf.config['colors'])
