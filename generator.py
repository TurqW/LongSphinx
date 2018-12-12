import random
import logging
import yaml
from num2words import num2words
import re
import configmanager
import mcgenerator
log = logging.getLogger('LongSphinx.Generators')

conf = {}

def generate(name):
	if name.startswith('mc:'):
		#TODO: There may be a less hardcoded way to do this.
		return mcgenerator.generate(name[3:])
	if name.startswith('num:'):
		rangeends = name.strip("num: ").split('-')
		return num2words(random.randrange(int(rangeends[0]), int(rangeends[1])))
	parsed_name = name.split('.')
	generator = parsed_name[0]
	load_config(generator)
	if len(parsed_name) == 1:
		mystring = random.choice(conf[generator].config['root'])
	else:
		option_set = conf[generator].config
		for level in parsed_name[1:]:
			option_set = option_set[level]
		mystring = random.choice(option_set)
	return populate_string(mystring)
	

def populate_string(mystring):
	for toReplace in re.findall(r'{[\w.:-]+}', mystring):
		mystring = mystring.replace(toReplace, generate(toReplace[1:-1]), 1)
	return fix_articles(mystring)

def fix_articles(mystring):
	# relevant: https://stackoverflow.com/questions/2763750/how-to-replace-only-part-of-the-match-with-python-re-sub
	return re.sub(r"(^|\W)a( [aAeEiIoOuU](?!ni))", r'\1an\2', mystring)

def load_config(name):
	if name not in conf:
		conf[name] = configmanager.ConfigManager('genConfig/{0}.yaml'.format(name))
	conf[name].update_config()

def readme(generators):
	msg = ''
	for gen_name in generators:
		load_config(gen_name)
		msg += '* `!' + gen_name + '`: %s\n' % (conf[gen_name].config['description'])
	
	return msg
