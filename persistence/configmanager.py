import logging
import os

import yaml

log = logging.getLogger('LongSphinx.ConfigManager')


class ConfigManager:

    def __init__(self, filename, bot_name='universal'):
        self.lastmod = os.stat(filename).st_mtime
        self.filename = filename
        self.botName = bot_name
        with open(filename, 'r') as stream:
            try:
                self.config = yaml.load(stream, Loader=yaml.Loader)
            except yaml.YAMLError as exc:
                log.exception(exc)
                print('Configuration load failed for {0}'.format(filename))

    def update_config(self):
        newlastmod = os.stat(self.filename).st_mtime
        if newlastmod > self.lastmod:
            log.info('New {0} found. Loading...'.format(self.filename))
            with open(self.filename, 'r') as stream:
                try:
                    self.config = yaml.load(stream, Loader=yaml.Loader)
                    self.lastmod = newlastmod
                except yaml.YAMLError as exc:
                    log.exception(exc)
                    log.error('YAML invalid, sticking with version from {0}'.format(self.lastmod))
