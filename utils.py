import os

def check_path(name):
	if not os.path.exists(name):
		os.makedirs(name)