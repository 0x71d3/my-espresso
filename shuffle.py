import random
import sys

random.seed(0)

pairs = []
for line in iter(sys.stdin.readline, ''):
    pair = line.strip().split('\t')
    pairs.append(pair)

random.shuffle(pairs)

for pair in pairs:
    print('\t'.join(pair))
