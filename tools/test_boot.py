# boot.py の訳の仕組み（T・wrap）をゲームなしで試す。libtcodpy は偽物を使う。
# 使い方: python tools/test_boot.py "英語の文" ...
import sys, types, os, textwrap
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
fake = types.ModuleType('libtcodpy')
for n in ['console_set_custom_font', 'console_map_ascii_code_to_font', 'console_print', 'console_print_ex',
          'console_put_char', 'console_flush', 'console_get_background_flag', 'console_get_alignment']:
	setattr(fake, n, lambda *a, **k: None)
fake.CENTER, fake.RIGHT, fake.LEFT = 1, 2, 0
sys.modules['libtcodpy'] = fake
src = open(os.path.join(ROOT, 'ja', 'boot.py'), encoding='utf8').read()
src = src[:src.index('_ja_src = ')]          # ゲーム本体は動かさない
os.chdir(ROOT)
g = {'__name__': 'test'}
exec(compile(src, 'boot.py', 'exec'), g)
T = g['_ja_T']
for s in sys.argv[1:] or ['Continue', 'After 3 days in the field hospital, you recover and return to active duty on June 5, 1944',
                         'Standard Campaign', '2 crewmen were KIA while you were in the field hospital.']:
	print(repr(s), '->', repr(T(s)))
print(textwrap.wrap('You are protected by fate, giving you the option of negating a few incoming attacks per day that might otherwise destroy your vehicle.', 30))
