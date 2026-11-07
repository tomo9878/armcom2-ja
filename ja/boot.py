# Armoured Commander II 日本語化の起動スクリプト。
# 差し替えた armcom2.exe が最初にこれを実行する（日本語化ツール／tools\patch_exe.py）。
# やること:
#   1. 日本語の字を足したフォント（ja\font_NN.png）を使わせ、字の位置を割り当てる
#   2. 画面に文字を書く関数（console_print / console_print_ex / textwrap.wrap）に
#      英語→日本語の表（ja\strings_ja.json）を挟む。ゲームの処理は英語の文字列で
#      判定しているので、ソースの文字列は書き換えず「表示する直前」に訳す
#   3. ゲーム付属のソース src\armcom2.py を読み、必要な所だけメモリ上で直して実行する（_JA_PATCHES）
import os as _ja_os, sys as _ja_sys, json as _ja_json, re as _ja_re, textwrap as _ja_textwrap

_JA_DIR = 'ja'


def _ja_log(msg):
	try:
		with open(_ja_os.path.join(_JA_DIR, 'boot_log.txt'), 'a', encoding='utf8') as f:
			f.write(str(msg) + '\n')
	except Exception:
		pass


def _ja_cp850(s):
	"""ゲームの line.encode('IBM850') の代わり（_JA_PATCHES で置換）。日本語を含むなら文字列のまま返す"""
	try:
		return s.encode('IBM850')
	except UnicodeEncodeError:
		return s


def _ja_setup():
	import libtcodpy as libtcod

	table = {}
	p = _ja_os.path.join(_JA_DIR, 'strings_ja.json')
	if _ja_os.path.exists(p):
		with open(p, encoding='utf8') as f:
			table = {k: v for k, v in _ja_json.load(f).items() if v}
	# 組み立てた文の型: [英語の型 '{0} spotted by air support!', 日本語の型 '{0}が航空支援に発見された！']
	templates = []
	p = _ja_os.path.join(_JA_DIR, 'templates_ja.json')
	if _ja_os.path.exists(p):
		with open(p, encoding='utf8') as f:
			for en, ja in _ja_json.load(f).items():
				if not ja:
					continue
				parts = _ja_re.split(r'(\{\d+\})', en)
				lits = [x.replace('{{', '{').replace('}}', '}') for x in parts[0::2]]
				rx = ''
				for i, x in enumerate(parts):
					rx += _ja_re.escape(lits[i // 2]) if i % 2 == 0 else '(.+?)'
				order = [int(x[1:-1]) for x in parts[1::2]]
				key = max(lits, key=len)
				templates.append((len(''.join(lits)), key, _ja_re.compile('^' + rx + '$', _ja_re.S), order, ja))
	templates.sort(key=lambda t: -t[0])
	with open(_ja_os.path.join(_JA_DIR, 'font_chars.txt'), encoding='utf8') as f:
		chars = f.read().rstrip('\r\n')   # 先頭は全角スペース（U+3000）。strip() すると消えて字の位置が1つずれる
	missing = set()
	cjk_any = _ja_re.compile('[぀-ヿ一-鿿]')   # 日本語を含む行（訳済みを切り詰めたもの）は記録しない
	memo = {}

	def T(s, depth=0):
		if not isinstance(s, str) or not s:
			return s
		v = memo.get(s)
		if v is not None:
			return v
		v = _T(s, depth)
		if len(memo) > 50000:
			memo.clear()
		memo[s] = v
		return v

	def _T(s, depth):
		v = table.get(s)
		if v is not None:
			return v
		core = s.strip()
		if core != s and core in table:
			i = s.index(core)
			return s[:i] + table[core] + s[i+len(core):]
		if depth < 3 and core:
			for n, key, rx, order, ja in templates:
				if key not in core:
					continue
				m = rx.match(core)
				if m:
					vals = [T(g, depth + 1) for g in m.groups()]
					args = [''] * (max(order) + 1 if order else 0)
					for k, g in zip(order, vals):
						args[k] = g
					try:
						out = ja.format(*args)
					except Exception:
						continue
					i = s.index(core)
					return s[:i] + out + s[i+len(core):]
		# 「France, United Kingdom, Belgium」のような並びは1つずつ訳して「、」でつなぐ（全部訳せたときだけ）
		if depth < 3 and ', ' in core:
			parts = core.split(', ')
			outs = [T(x, depth + 1) for x in parts]
			if all(o != x for o, x in zip(outs, parts)):
				i = s.index(core)
				return s[:i] + '、'.join(outs) + s[i+len(core):]
		# 訳し漏れの記録（略語・クラッシュ画面の文は除く）
		if depth == 0 and core and _ja_re.search('[A-Za-z]{2}', core) and not _ja_re.fullmatch(r'[A-Z0-9()/ +-]{1,6}', core) \
				and 'File "' not in core and 'Traceback' not in core and not cjk_any.search(core):
			note_missing(core)
		return s

	# 訳し漏れは見つけたその場で ja\missing.txt に追記する（ウィンドウの×などで落ちても残るように）。
	# 前回までの分は消さずに読み込み、同じ文は2度書かない。改行は \n と書く
	missing_path = _ja_os.path.join(_JA_DIR, 'missing.txt')
	try:
		with open(missing_path, encoding='utf8') as f:
			missing.update(line.rstrip('\n') for line in f if line.strip())
	except Exception:
		pass

	def note_missing(core):
		key = core.replace('\n', '\\n')
		if key in missing:
			return
		missing.add(key)
		try:
			with open(missing_path, 'a', encoding='utf8') as f:
				f.write(key + '\n')
		except Exception:
			pass

	# --- フォント ---
	orig_font = libtcod.console_set_custom_font

	def set_font(fontFile, flags=None, nb_char_horiz=0, nb_char_vertic=0):
		m = _ja_re.search(r'(\d+)x\d+_ext\.png$', fontFile)
		ja_font = _ja_os.path.join(_JA_DIR, 'font_%s.png' % m.group(1)) if m else None
		if ja_font and 'dys_' not in fontFile and _ja_os.path.exists(ja_font):
			rows = 18 + (len(chars) + 15) // 16
			orig_font(ja_font, flags, 16, rows)
			# 字 i は画像の 288+i 番目のマス（16列×18行の元のフォントの後ろ）
			for i, c in enumerate(chars):
				n = 16 * 18 + i
				libtcod.console_map_ascii_code_to_font(ord(c), n % 16, n // 16)
			_ja_log('font ' + ja_font)
		else:
			orig_font(fontFile, flags, nb_char_horiz, nb_char_vertic)
	libtcod.console_set_custom_font = set_font

	# --- 文字列 ---
	orig_print = libtcod.console_print
	orig_print_ex = libtcod.console_print_ex

	# libtcod の print は全角の字を2マス分進めるので、日本語を含む文字列は1字ずつ put_char で書く
	wide = _ja_re.compile('[ -⯿　-鿿＀-￯]')

	# 日本語の行の英数字・記号は、元の太いC64の字ではなく日本語フォントの全角の字（Ａ、１）で描く（ユーザー指定: 字体をそろえる）。
	# 全角の字がフォントに無い " ' は全角の引用符で代用
	zen = {i: i + 0xFEE0 for i in range(0x21, 0x7F) if chr(i + 0xFEE0) in chars}
	zen[ord('"')] = 0x201D
	zen[ord("'")] = 0x2019

	def put_text(con, x, y, flag, alignment, s):
		s = s.translate(zen)
		for row, line in enumerate(s.split('\n')):
			if alignment == libtcod.CENTER:
				cx = x - len(line) // 2
			elif alignment == libtcod.RIGHT:
				cx = x - len(line) + 1
			else:
				cx = x
			for c in line:
				libtcod.console_put_char(con, cx, y + row, ord(c), flag)
				cx += 1

	def console_print(con, x, y, fmt):
		s = T(fmt)
		if isinstance(s, str) and wide.search(s):
			return put_text(con, x, y, libtcod.console_get_background_flag(con), libtcod.console_get_alignment(con), s)
		return orig_print(con, x, y, s)

	def console_print_ex(con, x, y, flag, alignment, fmt):
		s = T(fmt)
		if isinstance(s, str) and wide.search(s):
			return put_text(con, x, y, flag, alignment, s)
		return orig_print_ex(con, x, y, flag, alignment, s)
	libtcod.console_print = console_print
	libtcod.console_print_ex = console_print_ex

	orig_wrap = _ja_textwrap.wrap
	cjk = _ja_re.compile('[　-ヿ一-鿿＀-￯]')
	no_head = set('、。，．・ー」』）！？：％')

	def wrap(text, width=70, **kw):
		text = T(text)
		if not isinstance(text, str) or not cjk.search(text):
			return orig_wrap(text, width, **kw)
		# 日本語: 英数字の続きは切らずに、字数で折り返す（行頭の句読点は前の行へ）
		lines = []
		for para in text.split('\n'):
			cur = ''
			for tok in _ja_re.findall(r"[A-Za-z0-9.,'%/()+\-]+|.", para):
				if len(cur) + len(tok) > width and cur.strip() and not (len(tok) == 1 and tok in no_head):
					lines.append(cur.rstrip())
					cur = tok.lstrip()
				else:
					cur += tok
			if cur.strip():
				lines.append(cur.rstrip())
		return lines
	_ja_textwrap.wrap = wrap

	return T


try:
	_ja_T = _ja_setup()
except Exception:
	import traceback as _ja_tb
	_ja_log(_ja_tb.format_exc())

# ゲーム付属のソース（src\armcom2.py）を読み、日本語表示に必要な所だけメモリ上で直して実行する。
# ソースの写しは配らない。ゲームが更新されて元の文字列が見つからない所は飛ばす（その部分だけ英語のまま／日本語で落ちうる）
_JA_PATCHES = [
	# 名前の表示（PrintExtended）: IBM850 に無い字（日本語）はそのまま文字コードで出す
	("\t\t\tchar_code = ord(char.encode('IBM850', errors='replace'))\n",
	 "\t\t\ttry: char_code = ord(char.encode('IBM850'))\n\t\t\texcept UnicodeEncodeError: char_code = ord(char)\n", 1),
	# メッセージの行を IBM850 のバイト列にして書く所（日本語は変換できず落ちる）
	("line.encode('IBM850'))", "_ja_cp850(line))", 3),
	# 日付: "June 5, 1944" → "1944年6月5日"
	("\treturn (MONTH_NAMES[int(date_list[1].lstrip('0'))] + ' ' + str(date_list[2].lstrip('0')) + \n\t\t', ' + date_list[0])\n",
	 "\treturn date_list[0] + '年' + date_list[1].lstrip('0') + '月' + date_list[2].lstrip('0') + '日'\n", 1),
]
def _ja_rank(name):
	"""階級名を日本語に（表に無ければそのまま）"""
	t = _ja_T(name.strip())
	return t if isinstance(t, str) else name

def _ja_rank(name):
	"""階級名を日本語に（表に無ければそのまま）"""
	t = _ja_T(name.strip())
	return t if isinstance(t, str) else name

_ja_src = _ja_os.path.join('src', 'armcom2.py')
with open(_ja_src, encoding='utf8') as _ja_f:
	_ja_text = _ja_f.read()
for _ja_old, _ja_new, _ja_n in _JA_PATCHES:
	if _ja_text.count(_ja_old) == _ja_n:
		_ja_text = _ja_text.replace(_ja_old, _ja_new)
	else:
		_ja_log('source patch skipped (%d != %d): %r' % (_ja_text.count(_ja_old), _ja_n, _ja_old[:50]))
# 階級名の表示（比較に使う rank_name = の行は除く）
_ja_text = _ja_re.sub(r"(?<!rank_name = )(session\.nations\[[^\]]+\]\['rank_names'\]\[str\([^)]*\)\])",
	lambda m: '_ja_rank(' + m.group(1) + ')', _ja_text)
# 階級名の表示（比較に使う rank_name = の行は除く）
_ja_text = _ja_re.sub(r"(?<!rank_name = )(session\.nations\[[^\]]+\]\['rank_names'\]\[str\([^)]*\)\])",
	lambda m: '_ja_rank(' + m.group(1) + ')', _ja_text)
exec(compile(_ja_text, _ja_src, 'exec'))
