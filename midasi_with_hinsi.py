import sys
from pyknp import Juman

jumanpp = Juman()

half2full = str.maketrans(
    '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
    '０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［＼］＾＿‘｛｜｝～',
)

all_hinsis = [
    '*', '特殊', '動詞', '形容詞', '判定詞', '助動詞', '名詞', '指示詞',
    '副詞', '助詞', '接続詞', '連体詞', '感動詞', '接頭辞', '接尾辞', '未定義語'
]

for line in iter(sys.stdin.readline, ''):
    try:
        full_line = line.strip().translate(half2full)
        result = jumanpp.analysis(full_line)

        midasis = []
        hinsis = []
        for mrph in result.mrph_list():
            midasis.append(mrph.midasi)
            hinsis.append(all_hinsis.index(mrph.hinsi))
        
        print(' '.join(midasis) + '\t' + ' '.join(map(str, hinsis)))

    except:
        jumanpp = Juman()
