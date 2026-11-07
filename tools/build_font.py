# 元のフォント画像（16列×18行の c64_*_ext.png）の下に日本語の字を足した画像を作る。
# 足した字の並びは ja\font_chars.txt（1行に全部）。boot.py が読み込んで字の位置を割り当てる。
# 使い方: python build_font.py   （ゲームの data と ja\strings_ja.json を見る）
import json, os
from PIL import Image, ImageDraw, ImageFont

GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Armoured Commander II'
HERE = os.path.dirname(os.path.abspath(__file__))
JA = os.path.join(HERE, '..', 'ja')
COLS, BASE_ROWS = 16, 18
FONT = r'C:\Windows\Fonts\msgothic.ttc'   # 12/16px は埋め込みビットマップでくっきり出る


def charset():
    chars = []
    seen = set()
    def add(c):
        if c not in seen and ord(c) > 0xFF:
            seen.add(c); chars.append(c)
    # cp932 の記号・英数・かな（0x81〜0x84）と第1水準漢字（0x889F〜0x9872）
    for lead in list(range(0x81, 0x85)) + list(range(0x88, 0x99)):
        for trail in range(0x40, 0xFD):
            try:
                c = bytes([lead, trail]).decode('cp932')
            except UnicodeDecodeError:
                continue
            if lead == 0x98 and trail > 0x72:
                continue
            add(c)
    # 訳文に出てくる字（第2水準など）
    p = os.path.join(JA, 'strings_ja.json')
    if os.path.exists(p):
        for v in json.load(open(p, encoding='utf8')).values():
            for c in v:
                add(c)
    for c in '・ー〜…「」『』（）！？：、。％＋－':
        add(c)
    return chars


def build(size, chars, src_name, dst_name):
    base = Image.open(os.path.join(GAME, 'data', src_name)).convert('RGBA')
    rows = BASE_ROWS + (len(chars) + COLS - 1) // COLS
    im = Image.new('RGBA', (COLS * size, rows * size), (0, 0, 0, 0))
    im.paste(base, (0, 0))
    font = ImageFont.truetype(FONT, size)
    for i, c in enumerate(chars):
        n = COLS * BASE_ROWS + i
        x, y = (n % COLS) * size, (n // COLS) * size
        g = Image.new('L', (size, size), 0)
        d = ImageDraw.Draw(g)
        d.fontmode = '1'
        d.text((0, 0), c, font=font, fill=255)
        im.paste(Image.new('RGBA', (size, size), (255, 255, 255, 255)), (x, y), g)
    im.save(os.path.join(JA, dst_name))
    return im.size


if __name__ == '__main__':
    chars = charset()
    open(os.path.join(JA, 'font_chars.txt'), 'w', encoding='utf8').write(''.join(chars))
    for s in (8, 12, 16):
        print(s, build(s, chars, 'c64_%dx%d_ext.png' % (s, s), 'font_%d.png' % s))
    print('chars', len(chars))
