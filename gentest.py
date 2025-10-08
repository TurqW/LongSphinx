from generators import generator
from os import listdir
from os.path import isfile, join
import sys

if len(sys.argv) > 1:
    for _ in range(1000):
        print(generator.extract_text(generator.generate(sys.argv[1])))
else:
    files = [f for f in listdir('genConfig') if isfile(join('genConfig', f))]

    for file in files:
        print(file)
        for _ in range(1000):
            print(generator.extract_text(generator.generate(file.split('.')[0])))
