# 兵器解説の翻訳の続き用。
#   python tools/units_next.py          … まだ訳していない最初のチャンクを表示（行番号<TAB>兵器名<TAB>英語）
#   python tools/units_next.py apply    … 訳の表を作り直してゲームに入れる（チャンクを1つ訳すたびに実行）
#   python tools/units_next.py status   … 進み具合
# 英語は tr/en/unit_NNN.txt（extract_strings.extract_units() で作成、作り直さない）、訳は tr/unit_NNN.tsv（行番号<TAB>日本語）。
# 001〜023 が独米英日ソの車両、024〜032 がほかの国の車両、033〜038 が砲、039〜044 が航空機・歩兵など。
import glob, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')


def chunks():
	return sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(ROOT, 'tr', 'en', 'unit_*.txt')))


def done(c):
	return os.path.exists(os.path.join(ROOT, 'tr', c + '.tsv'))


sys.stdout.reconfigure(encoding='utf-8')
cmd = sys.argv[1] if len(sys.argv) > 1 else 'next'
if cmd == 'apply':
	for s in ('build_table.py', 'build_font.py', 'install.py'):
		subprocess.check_call([sys.executable, os.path.join(HERE, s)])
elif cmd == 'status':
	cs = chunks()
	ok = [c for c in cs if done(c)]
	print('訳し済み %d / %d チャンク' % (len(ok), len(cs)), ' '.join(c[5:] for c in ok))
else:
	todo = [c for c in chunks() if not done(c)]
	if not todo:
		print('全部訳し済み')
	else:
		c = todo[0]
		print('#', c, '（残り %d チャンク）' % len(todo))
		for i, line in enumerate(open(os.path.join(ROOT, 'tr', 'en', c + '.txt'), encoding='utf8'), 1):
			name, en = line.rstrip('\n').split('\t', 1)
			print('%d\t%s\t%s' % (i, name, en))
