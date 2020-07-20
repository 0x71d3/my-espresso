import glob
import re

for wiki_file in sorted(glob.glob('**/wiki_*', recursive=True)):
    with open(wiki_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not re.match(r'</?doc.*>', line):
                sentences = re.findall(r'[^。]+。?', line)
                if len(sentences) > 1:
                    for sentence in sentences[:-1]:
                        print(sentence)
