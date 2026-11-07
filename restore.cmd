@echo off
rem Armoured Commander II を英語の元の状態に戻す（exe を元に戻し、ja フォルダを消す）
set GAME=C:\Program Files (x86)\Steam\steamapps\common\Armoured Commander II
copy /Y "%~dp0orig\armcom2.exe" "%GAME%\armcom2.exe"
if exist "%GAME%\ja" rmdir /S /Q "%GAME%\ja"
echo 元に戻しました。
pause
