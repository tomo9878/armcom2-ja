# 配布用の ZIP を作る: dist\ArmCom2_JA_<日付>\（ArmCom2_JA.exe・元に戻す.cmd・README.txt・ja\）と同名の .zip
# ゲームのファイル（exe・ソース・フォント画像）は入れない。フォントは遊ぶ人の PC で ArmCom2_JA.exe が作る。
# 使い方: python tools/make_dist.py
import os, shutil, subprocess, sys, datetime, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
DOTNET = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'dotnet-sdk', 'dotnet.exe')

subprocess.check_call([sys.executable, os.path.join(HERE, 'build_table.py')])
subprocess.check_call([sys.executable, os.path.join(HERE, 'build_font.py')])   # font_chars.txt を作り直す
build = os.path.join(ROOT, 'work', 'patcher_build')
subprocess.check_call([DOTNET, 'build', os.path.join(HERE, 'JaPatcher'), '-c', 'Release', '-o', build, '-v', 'q'])

name = 'ArmCom2_JA_' + datetime.date.today().strftime('%Y%m%d')
out = os.path.join(ROOT, 'dist', name)
shutil.rmtree(out, ignore_errors=True)
os.makedirs(os.path.join(out, 'ja'))
for f in ('ArmCom2_JA.exe', 'ArmCom2_JA.exe.config'):
	shutil.copy2(os.path.join(build, f), out)
for f in ('boot.py', 'strings_ja.json', 'templates_ja.json', 'font_chars.txt'):
	shutil.copy2(os.path.join(ROOT, 'ja', f), os.path.join(out, 'ja'))
shutil.copy2(os.path.join(ROOT, 'dist_files', 'README.txt'), out)
shutil.copy2(os.path.join(ROOT, 'dist_files', 'survivor_guide.html'), out)
with open(os.path.join(out, '元に戻す.cmd'), 'w', encoding='cp932', newline='\r\n') as f:
	f.write('@echo off\n"%~dp0ArmCom2_JA.exe" --restore\n')

zpath = out + '.zip'
with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
	for dp, _, fs in os.walk(out):
		for f in fs:
			p = os.path.join(dp, f)
			z.write(p, os.path.join(name, os.path.relpath(p, out)))
print(zpath, os.path.getsize(zpath), 'bytes')
for dp, _, fs in os.walk(out):
	for f in fs:
		print(' ', os.path.relpath(os.path.join(dp, f), out))
