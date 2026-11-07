# 日本語化をゲームに入れる: ja\ の中身をゲームの ja\ へコピーし、armcom2.exe を差し替える。
# 元の exe は ..\orig\armcom2.exe（戻すときは restore.cmd）。
import os, shutil, hashlib, subprocess, sys
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Armoured Commander II'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
ORIG = os.path.join(ROOT, 'orig', 'armcom2.exe')
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
if not os.path.exists(ORIG):
	sys.exit('orig/armcom2.exe がありません')
dst_ja = os.path.join(GAME, 'ja')
os.makedirs(dst_ja, exist_ok=True)
for f in ['boot.py', 'strings_ja.json', 'templates_ja.json', 'font_chars.txt', 'font_8.png', 'font_12.png', 'font_16.png']:
	shutil.copy2(os.path.join(ROOT, 'ja', f), os.path.join(dst_ja, f))
# exe は中身が同じなら書き換えない（ゲームを起動中でも訳の更新だけはできる）
built = os.path.join(ROOT, 'work', 'armcom2_ja.exe')
subprocess.check_call([sys.executable, os.path.join(HERE, 'patch_exe.py'), ORIG, built])
if md5(built) != md5(os.path.join(GAME, 'armcom2.exe')):
	shutil.copy2(built, os.path.join(GAME, 'armcom2.exe'))
print('installed. exe md5', md5(os.path.join(GAME, 'armcom2.exe')), '(orig', md5(ORIG) + ')')
