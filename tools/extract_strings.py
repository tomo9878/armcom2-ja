# ソース（orig\armcom2.py）とデータ JSON から訳す文字列を抜き出す。
#   work\ui_en.json   … ソースの文字列。kind=exact（そのまま一致）/ tmpl（'A ' + x + ' B' のような組み立て。{0}{1}… が差し込み）
#   work\data_en.json … 用語集・スキル・チュートリアル・乗員などのデータ JSON の文
# 訳は tr\*.json（{英語: 日本語}）に書き、build_table.py で ja\strings_ja.json / ja\templates_ja.json にまとめる。
import ast, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Armoured Commander II'
WORK = os.path.join(ROOT, 'work')

TEXTY = re.compile(r'[A-Za-z]{2}')


def is_text(s):
	"""画面に出そうな文か（内部キー・ファイル名などを除く）"""
	t = s.strip()
	if not TEXTY.search(t):
		return False
	if re.fullmatch(r'[a-z0-9_]+', t):          # snake_case のキー
		return False
	if re.search(r'\.(json|xp|png|ogg|wav|txt|cfg|dat)$', t) or '\\' in t or t.startswith('#'):
		return False
	if re.fullmatch(r'[A-Z0-9_]+', t) and '_' in t:
		return False
	return True


def flatten_add(node):
	if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
		return flatten_add(node.left) + flatten_add(node.right)
	return [node]


def parts_of(node):
	"""組み立て式を [文字列 or 式の文字列] に分ける。文字列が無ければ None"""
	if isinstance(node, ast.JoinedStr):
		items = node.values
	elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
		items = flatten_add(node)
	else:
		return None
	out = []
	for it in items:
		if isinstance(it, ast.Constant) and isinstance(it.value, str):
			out.append(it.value)
		elif isinstance(it, ast.FormattedValue):
			out.append(('expr', ast.unparse(it.value)))
		else:
			out.append(('expr', ast.unparse(it)))
	if not any(isinstance(p, str) and TEXTY.search(p) for p in out):
		return None
	return out   # 文字列だけの連結（長文を行で分けたもの）は呼び出し側で exact にする


def main():
	src = open(os.path.join(ROOT, 'orig', 'armcom2.py'), encoding='utf8').read()
	tree = ast.parse(src)
	# 関数名を行に対応させる（文脈用）
	func_at = {}
	for node in ast.walk(tree):
		if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
			for n in ast.walk(node):
				if hasattr(n, 'lineno'):
					func_at.setdefault(n.lineno, node.name) if isinstance(node, ast.ClassDef) else func_at.__setitem__(n.lineno, node.name)
	entries = collections.OrderedDict()
	in_tmpl = set()
	for node in ast.walk(tree):
		p = parts_of(node)
		if p is None:
			continue
		# 外側の組み立て式だけ使う（内側の部分式は飛ばす）
		for sub in ast.walk(node):
			if sub is not node:
				in_tmpl.add(id(sub))
		if id(node) in in_tmpl:
			continue
		en, exprs = '', []
		for x in p:
			if isinstance(x, str):
				en += x.replace('{', '{{').replace('}', '}}')
			else:
				en += '{%d}' % len(exprs)
				exprs.append(x[1])
		if not exprs:
			en = ''.join(p)
			if is_text(en) and en not in entries:
				entries[en] = {'en': en, 'kind': 'exact', 'line': node.lineno, 'func': func_at.get(node.lineno, '')}
		elif en not in entries:
			entries[en] = {'en': en, 'kind': 'tmpl', 'line': node.lineno,
			               'func': func_at.get(node.lineno, ''), 'args': exprs}
	for node in ast.walk(tree):
		if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in in_tmpl:
			s = node.value
			if is_text(s) and s not in entries and len(s) < 2000:
				entries[s] = {'en': s, 'kind': 'exact', 'line': node.lineno, 'func': func_at.get(node.lineno, '')}
	# 組み立て式の中の文字列も、単独で表示されることがあるので exact として残す
	for node in ast.walk(tree):
		if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) in in_tmpl:
			s = node.value
			if is_text(s) and s.strip() not in entries and len(s.strip()) > 1:
				pass  # 断片は訳さない（型で訳す）
	items = sorted(entries.values(), key=lambda e: e['line'])
	os.makedirs(WORK, exist_ok=True)
	json.dump(items, open(os.path.join(WORK, 'ui_en.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
	c = collections.Counter(e['kind'] for e in items)
	print('ui', dict(c), 'words', sum(len(e['en'].split()) for e in items))

	# --- データ JSON ---
	data = []
	def add(file, path, s):
		if isinstance(s, str) and TEXTY.search(s):
			data.append({'file': file, 'path': path, 'en': s})
	g = json.load(open(os.path.join(GAME, 'data', 'glossary.json'), encoding='utf8'))
	for k, v in g['English'].items():     # German もあるが英語版だけ訳す
		add('glossary', k, k)
		add('glossary', k + '/def', v)
	sk = json.load(open(os.path.join(GAME, 'data', 'skill_defs.json'), encoding='utf8'))
	for k, v in sk.items():
		add('skill', k, k)
		add('skill', k + '/desc', v.get('desc'))
	tu = json.load(open(os.path.join(GAME, 'data', 'tutorial_slides.json'), encoding='utf8'))
	def walk(o, path, file):
		if isinstance(o, dict):
			for k, v in o.items():
				walk(v, path + '/' + k, file)
		elif isinstance(o, list):
			for i, v in enumerate(o):
				walk(v, path + '/%d' % i, file)
		else:
			add(file, path, o)
	walk(tu, '', 'tutorial')
	for f in ('crew_command_defs', 'crew_talk'):
		walk(json.load(open(os.path.join(GAME, 'data', f + '.json'), encoding='utf8')), '', f)
	seen, uniq = set(), []
	for d in data:
		if d['en'] not in seen and d['en'] not in entries:
			seen.add(d['en']); uniq.append(d)
	json.dump(uniq, open(os.path.join(WORK, 'data_en.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
	print('data', collections.Counter(d['file'] for d in uniq), 'words', sum(len(d['en'].split()) for d in uniq))


if __name__ == '__main__':
	main()


def extract_weeks():
	"""キャンペーンの週の見出し・説明・コメントなどを tr/en/week_NN.txt に（キャンペーン順、見出しと説明を並べて）書き出す。
	一度作ったら作り直さない（訳の行番号がずれる）"""
	import glob
	seen, rows = set(), []
	skip = ('name', 'desc', 'creator', 'last_updated', 'difficulty', 'start_date', 'end_date', 'player_nation', 'region')
	for f in sorted(glob.glob(os.path.join(GAME, 'campaigns', '*.json'))):
		c = json.load(open(f, encoding='utf8'))
		camp = os.path.basename(f)[:-5]
		def add(k, v):
			if isinstance(v, str) and TEXTY.search(v) and v not in seen:
				seen.add(v); rows.append((camp + '/' + k, v))
		for k, v in c.items():
			if k not in skip and isinstance(v, str) and re.search('[a-z]{3} ', v):
				add(k, v)
		for w in c.get('calendar_weeks', []):
			for k in ('week_title', 'week_description'):
				add(k, w.get(k))
	N = 60
	for i in range(0, len(rows), N):
		with open(os.path.join(ROOT, 'tr', 'en', 'week_%02d.txt' % (i // N + 1)), 'w', encoding='utf8') as fo:
			for ctx, v in rows[i:i+N]:
				fo.write('%s\t%s\n' % (ctx, json.dumps(v, ensure_ascii=False)))
	print('weeks', len(rows), 'files', (len(rows) + N - 1) // N)


def extract_units():
	"""兵器解説（unit_type_defs.json の description を連結した文）を優先順に tr/en/unit_NNN.txt（30件ずつ）へ書き出す。
	優先: ①独米英日ソの車両 ②ほかの国の車両 ③砲 ④航空機など。一度作ったら作り直さない（訳の行番号がずれる）。
	tr/unit_NNN.tsv があるチャンクは訳し済み（進み具合はファイルの有無で分かる）"""
	d = json.load(open(os.path.join(GAME, 'data', 'unit_type_defs.json'), encoding='utf8'))
	main = ['Germany', 'United States of America', 'United Kingdom', 'Empire of Japan', 'Soviet Union']
	def rank(item):
		k, v = item
		cat, nat = v.get('category'), v.get('origin_nation')
		if cat == 'Vehicle' and nat in main: return (0, main.index(nat))
		if cat == 'Vehicle': return (1, 0)
		if cat == 'Gun': return (2, 0)
		return (3, 0)
	seen, rows = set(), []
	for k, v in sorted(d.items(), key=rank):
		text = ''.join(v.get('description') or [])
		if text and TEXTY.search(text) and text not in seen:
			seen.add(text); rows.append((k, text))
	N = 30
	for i in range(0, len(rows), N):
		with open(os.path.join(ROOT, 'tr', 'en', 'unit_%03d.txt' % (i // N + 1)), 'w', encoding='utf8') as fo:
			for k, t in rows[i:i+N]:
				fo.write('%s\t%s\n' % (k, json.dumps(t, ensure_ascii=False)))
	print('units', len(rows), 'files', (len(rows) + N - 1) // N, 'words', sum(len(t.split()) for _, t in rows))
