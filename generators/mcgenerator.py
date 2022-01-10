import random
import logging
from persistence import configmanager

log = logging.getLogger('LongSphinx.Generators')

mcDataPath = 'genConfig/mcSources/'
conf = {}


def generate(name):
    if name not in conf:
        conf[name] = configmanager.ConfigManager(f'{mcDataPath}{name}.yaml')
    conf[name].update_config()
    return MName(conf[name].config).new()


class Mdict:
    def __init__(self):
        self.d = {}

    def __getitem__(self, key):
        if key in self.d:
            return self.d[key]
        else:
            raise KeyError(key)

    def add_key(self, prefix, suffix):
        if prefix in self.d:
            self.d[prefix].append(suffix)
        else:
            self.d[prefix] = [suffix]

    def get_suffix(self, prefix):
        l = self[prefix]
        return random.choice(l)


class MName:
    """
    A name from a Markov chain
    """

    def __init__(self, dataset, chainlen=2):
        """
        Building the dictionary
        """
        if chainlen > 10 or chainlen < 1:
            chainlen = 2

        self.mcd = Mdict()
        self.oldnames = []
        self.chainlen = chainlen

        for l in dataset:
            l = l.strip()
            self.oldnames.append(l)
            s = " " * chainlen + l
            for n in range(0, len(l)):
                self.mcd.add_key(s[n:n + chainlen], s[n + chainlen])
            self.mcd.add_key(s[len(l):len(l) + chainlen], "\n")

    def new(self):
        """
        New name from the Markov chain
        """
        attempts = 0
        while attempts < 5:
            prefix = " " * self.chainlen
            name = ""
            while True:
                suffix = self.mcd.get_suffix(prefix)
                if suffix == "\n" or len(name) > 99:
                    break
                else:
                    name = name + suffix
                    prefix = prefix[1:] + suffix
            if name not in self.oldnames:
                return name
        return name
