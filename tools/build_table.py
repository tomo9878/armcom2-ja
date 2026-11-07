# tr\*.json（{英語: 日本語}）をまとめて ja\strings_ja.json（完全一致）と ja\templates_ja.json（{0} 入りの型）を作る。
# 型かどうかは work\ui_en.json の kind で決める。訳が空のものは入れない。
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
ui = json.load(open(os.path.join(ROOT, 'work', 'ui_en.json'), encoding='utf8'))
tmpl_keys = {e['en'] for e in ui if e['kind'] == 'tmpl'}
strings, templates, bad = {}, {}, []
# 文字の部分が短すぎて、関係のない英文にも当たってしまう型（例: '{0}, and {1}' が説明文の ", and" を「、」に変えた）。使わない
BLOCK = {'{0}, and {1}', '{0} on', ' by {0}', '{0} {1} arrive', '{0} using {1}.', '{0} {1} detected',
         '{0} was', '{0} was ', '{0} moves'}
def load(f):
	r"""tr\*.json は {英語: 日本語}、tr\*.tsv は「行番号<TAB>日本語」で tr\en\同名.txt の行（<文脈><TAB>"英語"）に対応"""
	if f.endswith('.json'):
		return json.load(open(f, encoding='utf8')).items()
	src = open(os.path.join(ROOT, 'tr', 'en', os.path.basename(f)[:-4] + '.txt'), encoding='utf8').read().splitlines()
	out = []
	for line in open(f, encoding='utf8').read().splitlines():
		if not line.strip() or line.startswith('#'):
			continue
		n, ja = line.split('\t', 1)
		en = json.loads(src[int(n) - 1].rsplit('\t', 1)[1])
		out.append((en, ja.replace('\\n', '\n')))
	return out

for f in sorted(glob.glob(os.path.join(ROOT, 'tr', '*.json')) + glob.glob(os.path.join(ROOT, 'tr', '*.tsv'))):
	for en, ja in load(f):
		if not ja:
			continue
		if en in tmpl_keys or re.search(r'\{\d+\}', en):
			if en in BLOCK:
				continue
			if sorted(re.findall(r'\{\d+\}', en)) != sorted(re.findall(r'\{\d+\}', ja)):
				bad.append((os.path.basename(f), en, ja))
				continue
			templates[en] = ja
		else:
			strings[en] = ja
for b in bad:
	print('差し込みの数が合わない:', b)
json.dump(strings, open(os.path.join(ROOT, 'ja', 'strings_ja.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
json.dump(templates, open(os.path.join(ROOT, 'ja', 'templates_ja.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print('strings', len(strings), 'templates', len(templates))
