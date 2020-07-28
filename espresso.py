import csv
import math
import random
import re
import sys

from pyknp import Juman

all_pos_tags = [
    '*', '特殊', '動詞', '形容詞', '判定詞', '助動詞', '名詞', '指示詞',
    '副詞', '助詞', '接続詞', '連体詞', '感動詞', '接頭辞', '接尾辞', '未定義語'
]

half2full = str.maketrans(
    '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
    '０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［＼］＾＿‘｛｜｝～',
)

jumanpp = Juman()

x_label = '_x'
y_label = '_y'
tr_label = '_TR'

labels = [x_label, y_label, tr_label]

sentences = set()
pos_tag_dict = {}

pmis = {}
max_pmi = 0

instances = set()
patterns = set()

instance_reliabilities = {}
pattern_reliabilities = {}


def get_search_pattern(e):
    return '(^| )' + e + '( |$)'


def get_sub_pattern(l):
    return '\\1' + l + '\\2'


def get_pattern_freq(x=None, p=None, y=None):
    pattern_freq = 0

    if p is None:
        x_pattern = get_search_pattern(x)
        y_pattern = get_search_pattern(y)

        for s in sentences:
            if re.search(x_pattern, s) and re.search(y_pattern, s):
                pattern_freq += 1

    else:
        p_pattern = p

        p_pattern = re.sub(x_label, '(.+)' if x is None else x, p_pattern)  # instantiate x
        p_pattern = re.sub(y_label, '(.+)' if y is None else y, p_pattern)  # instantiate y

        p_pattern = re.sub(tr_label, '(.+)', p_pattern)

        for s in sentences:
            if re.match(p_pattern, s):
                pattern_freq += 1

    return pattern_freq


def set_pmi(i, p):
    global pmis

    x, y = i
    # print('(i, p) =', (i, p))

    xpy_freq = get_pattern_freq(x, p, y)      # |x, p, y|
    xy_freq = get_pattern_freq(x, None, y)    # |x, *, y|
    p_freq = get_pattern_freq(None, p, None)  # |*, p, *|
    # print('(|x, p, y|, |x, *, y|, |*, p, *|) =', (xpy_freq, xy_freq, p_freq))

    sentence_num = len(sentences)
    pmi = (math.log(xpy_freq / (xy_freq * p_freq) * sentence_num)
        if xpy_freq > 0 else 0
    )
    # print('pmi({}, \'{}\') = {}'.format(i, p, pmi))

    if i not in pmis:
        pmis[i] = {}
    pmis[i][p] = pmi


def get_pmi(i, p):
    return pmis[i][p]


def set_max_pmi():
    global max_pmi
    max_pmi = 0
    for i in instances:
        for p in patterns:
            set_pmi(i, p)
            pmi = get_pmi(i, p)
            if pmi > max_pmi:
                max_pmi = pmi


def get_max_pmi():
    global max_pmi
    return max_pmi


def set_pattern_reliability(p):
    global pattern_reliabilities
    weighted_sum = 0
    for i in instances:
        weighted_sum += (
            get_pmi(i, p) / get_max_pmi() * get_instance_reliability(i)
        )
    pattern_reliabilities[p] = weighted_sum / len(instances)


def set_instance_reliability(i):
    global instance_reliabilities
    weighted_sum = 0
    for p in patterns:
        weighted_sum += (
            get_pmi(i, p) / get_max_pmi() * get_pattern_reliability(p)
        )
    instance_reliabilities[i] = weighted_sum / len(patterns)


def get_pattern_reliability(p):
    global pattern_reliabilities
    return pattern_reliabilities[p]


def get_instance_reliability(i):
    global instance_reliabilities
    return instance_reliabilities[i]


def get_instance_confidence(i):
    global patterns
    T = 0
    instance_confidence = 0    
    for p in patterns:
        T += get_pattern_reliability(p)
        instance_confidence += get_pmi(i, p) * get_pattern_reliability(p)
    instance_confidence /= T
    return instance_confidence


def pattern_induction():
    global instances

    for i in instances:
        x, y = i

        x_pattern = get_search_pattern(x)
        y_pattern = get_search_pattern(y)

        x_sub_pattern = get_sub_pattern(x_label)
        y_sub_pattern = get_sub_pattern(y_label)

        for s in sentences:
            if re.search(x_pattern, s) and re.search(y_pattern, s):
                p = s

                p = re.sub(x_pattern, x_sub_pattern, p)
                p = re.sub(y_pattern, y_sub_pattern, p)

                # generalize
                tr_list = []

                s_tokens = s.split(' ')
                s_pos_tags = pos_tag_dict[s].split(' ')

                nouns = []
                for token, pos in zip(s_tokens, s_pos_tags):
                    if all_pos_tags[int(pos)] == '名詞':
                        nouns.append(token)
                    elif nouns:
                        tr_list.append(' '.join(nouns))
                        nouns = []
                if nouns:
                    tr_list.append(' '.join(nouns))

                for tr in tr_list:
                    tr_pattern = get_search_pattern(tr)
                    tr_sub_pattern = get_sub_pattern(tr_label)

                    p = re.sub(tr_pattern, tr_sub_pattern, p)

                patterns.add(p)


def pattern_ranking(k):
    global patterns

    set_max_pmi()
    for p in patterns:
        set_pattern_reliability(p)

    sorted_patterns = sorted(patterns, key=get_pattern_reliability)
    patterns = set(sorted_patterns[:k])


def instance_extraction(tau=0.3, m=200):
    global instances

    # retrieve
    for p in patterns:
        p_pattern = p

        p_pattern = re.sub(x_label, '(?P<x>.+)', p_pattern, 1)
        p_pattern = re.sub(y_label, '(?P<y>.+)', p_pattern, 1)

        p_pattern = re.sub('|'.join(labels), '(.+)', p_pattern)

        for s in sentences:
            if re.match(p_pattern, s):
                x = re.match(p_pattern, s)['x']
                y = re.match(p_pattern, s)['y']

                x_tokens = x.split(' ')
                y_tokens = y.split(' ')

                token2pos = dict(
                    zip(s.split(' '), map(int, pos_tag_dict[s].split(' ')))
                )

                for xy_token in x_tokens + y_tokens:
                    if all_pos_tags[token2pos[xy_token]] != '名詞':
                        break
                else:
                    i = (x, y)
                    instances.add(i)

    set_max_pmi()
    for i in instances:
        set_instance_reliability(i)

    # filter
    confident_instances = set()
    for i in instances:
        instance_confidence = get_instance_confidence(i)
        print('S({}) = {}'.format(i, instance_confidence))

        if instance_confidence > tau:
            confident_instances.add(i)

    sorted_instances = sorted(confident_instances, key=get_instance_reliability)
    instances = set(sorted_instances[:m])


num_sentences = 20000

with open('xaf', encoding='utf-8') as f:
    for line in f:
        sentence, pos_tags = line.strip().split('\t')

        sentences.add(sentence)
        pos_tag_dict[sentence] = pos_tags

# read seeds from a csvfile
with open('seeds.csv', encoding='utf-8', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        instance = ()
        for entity in row:
            result = jumanpp.analysis(entity)
            tokens = [mrph.midasi for mrph in result.mrph_list()]
            instance += (' '.join(tokens),)
        instances.add(instance)

# initialize instance reliabilities of seeds
for i in instances:
    instance_reliabilities[i] = 1.0

print('I =', instances)
print()

k = 0

for i in range(3):
    print('Iteration {}:'.format(i + 1))
    print()

    print('- Pattern induction')
    pattern_induction()

    print('P =', patterns)
    print()

    k = k + 1 if k else len(patterns)

    print('- Pattern ranking/selection')
    pattern_ranking(k)
    print()

    print('- Instance extraction')
    instance_extraction(0.1)

    print('I =', instances)
    print()

print('Result:')
print('I =', instances)

with open('output.csv', 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    for instance in sorted(instances):
        writer.writerow(list(instance))
