# 車両名（unit_type_defs.json のキー＝画面に出る名前）と愛称（nick_name）の日本語を作る → tr/units_names.json
# 対象: ドイツ・アメリカ・イギリス・日本・ソ連（＋ドイツが使ったチェコの戦車）の車両（category=Vehicle）。ユーザー指定（2026-11-03）。
# 規則（RULES）を上から順に当て、最後に末尾の括弧（(late) など）を訳す。どの規則も当たらなければ英語のまま。
# 使い方: python tools/unit_names.py   （当たらなかった名前を表示する）
import json, os, re
GAME = r'C:\Program Files (x86)\Steam\steamapps\common\Armoured Commander II'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NATIONS = ['Germany', 'United States of America', 'United Kingdom', 'Empire of Japan', 'Soviet Union', 'Czechoslovakia']

# 日本の車両は1台ずつ
JAPAN = {
	'Type 83 Light Tank': '八三式軽戦車', 'Type 92': '九二式重装甲車', 'Type 94 Te-Ke': '九四式軽装甲車 TK',
	'Type 95 So-Ki': '九五式装甲軌道車 ソキ', 'Type 97 Te-Ke': '九七式軽装甲車 テケ', 'Type 95 Ha-Go': '九五式軽戦車 ハ号',
	'Type 89 I-Go': '八九式中戦車 イ号', 'Type 91 SS-Ki': '装甲作業機 SS', 'Type 97 Chi-Ha': '九七式中戦車 チハ',
	'Type 1 Ho-Ni I': '一式七糎半自走砲 ホニI', 'Type 4 Ho-Ro': '四式十五糎自走砲 ホロ', 'Type 91 Armoured Car': '九一式装甲車',
	'Type 93 Armoured Car': '九三式装甲車', 'Type 98 So-Da': '九八式装甲運搬車 ソダ', 'Type 1 Ho-Ha': '一式半装軌装甲兵車 ホハ',
	'Type 98 20mm AA GC': '九八式20mm高射機関砲車', 'Type 1 Ho-Ki': '一式装甲兵車 ホキ', 'Type 94 Truck': '九四式六輪自動貨車',
	'Type 95 Scout Car': '九五式小型乗用車', 'Type 92 I-Ke': '九二式五屯牽引車 イケ', 'Type 92 Ni-Ku': '九二式八屯牽引車 ニク',
	'Type 94 Yo-Ke': '九四式四屯牽引車 ヨケ', 'Type 95 Ho-Fu': '九五式十三屯牽引車 ホフ', 'Type 98 Shi-Ke': '九八式四屯牽引車 シケ',
	'Type 98 Ro-Ke': '九八式六屯牽引車 ロケ', 'Type 96 AA Gun Tractor': '九六式高射砲牽引車', 'Type 80 Nissan': '日産80型トラック',
	'Type 1 Toyota KC': 'トヨタKC型トラック', 'Type 78 Landsverk L-131': 'ランツヴェルク L-131',
}

# 個別の名前（規則で作りにくいもの）
SINGLE = {
	'Panzer VIp': 'ティーガー(P)', 'Panzer VIe': 'ティーガーI', 'Panzer VIb': 'ティーガーII',
	'Panzer VD': 'パンターD型', 'Panzer V D': 'パンターD型', 'Panzer VG': 'パンターG型', 'Panzer V G': 'パンターG型',
	'Panzerjager Tiger': 'エレファント', 'Jagdpanzer V': 'ヤークトパンター', 'Jagdpanzer VI': 'ヤークトティーガー',
	'Pz.Sfl. V': 'シュトゥーラー・エミール', 'Sturmmoerserwagen 606/4': 'シュトゥルムティーガー',
	'Sturmpanzer I': 'I号15cm自走重歩兵砲', 'Sturmpanzer II': 'II号15cm自走重歩兵砲', 'Sturmpanzer IV': 'IV号突撃戦車',
	'StuH 42': '42式突撃榴弾砲', 'StuIG 33B': '33B突撃歩兵砲', 'StuG III Flammpanzer': 'III号突撃砲 火炎放射型',
	'Flammpanzer II': 'II号火炎放射戦車', 'Flammpanzer 38(t)': '38(t)火炎放射戦車', 'Flammpanzer III M': 'III号火炎放射戦車M型',
	'Panzerjager I': 'I号対戦車自走砲', 'Jagdpanzer 38(t)': '38(t)駆逐戦車', 'Jagdpanzer IV': 'IV号駆逐戦車',
	'Jagdpanzer IV/70': 'IV号駆逐戦車/70(V)', 'Jagdpanzer IV/70 (A)': 'IV号駆逐戦車/70(A)',
	'Flakpanzer I': 'I号対空戦車', 'Flakpanzer 38(t)': '38(t)対空戦車', 'Flakpanzer IV Wirbelwind': 'ヴィルベルヴィント',
	'Flakpanzer IV Mobelwagen': 'メーベルワーゲン', 'Kfz 1': 'キューベルワーゲン', 'Kfz. 15': 'Kfz.15 中型乗用車',
	'Volkswagen Type 166': 'シュビムワーゲン', '8.8cm FlaK 18 Sfl.': '8.8cm FlaK18 自走砲',
	'M2A4 Light Tank': 'M2A4軽戦車', 'Willys MB': 'ウィリスMB ジープ', 'Ford GPA': 'フォードGPA', 'M29 Weasel': 'M29 ウィーゼル',
	'M20 Utility Car': 'M20汎用装甲車', 'Matilda': 'マチルダI', 'MK VII Tetrarch': 'テトラーク', 'Mark VII': 'テトラーク',
	'Rolls Royce AC': 'ロールス・ロイス装甲車', 'Guy Armoured Car': 'ガイ装甲車', 'Daimler Scout Car': 'ダイムラー偵察車 ディンゴ',
	'Daimler Armoured Car': 'ダイムラー装甲車', 'Daimler Armoured Car CS': 'ダイムラー装甲車 CS',
	'BM-13': 'カチューシャ', 'T-20 Komsomolets': 'T-20 コムソモーレツ', 'Komintern': 'コミンテルン',
	'Voroshilovets': 'ヴォロシロヴェツ', 'STZ-5': 'STZ-5 スターリネッツ', 'ZIS-5 Truck': 'ZIS-5 トラック',
}

# 規則（正規表現 → 置換）。上から順にすべて当てる
ROMAN = r'(I|II|III|IV)'
RULES = [
	(r'^Panzer ' + ROMAN + r' ([A-Z][0-9]?|D/E)$', r'\1号戦車\2型'),
	(r'^Panzer (35|38)\(t\) ([A-Z])$', r'\1(t)戦車\2型'), (r'^Panzer (35|38)\(t\)$', r'\1(t)戦車'),
	(r'^Panzer ' + ROMAN + r' ([A-Z][0-9]?) ', r'\1号戦車\2型 '),
	(r'^StuG ' + ROMAN + r' ([A-Z])$', r'\1号突撃砲\2型'),
	(r'^StuG ' + ROMAN + r' ([A-Z]) ', r'\1号突撃砲\2型 '),
	(r'^StuG ' + ROMAN + r'$', r'\1号突撃砲'),
	(r'^StuG ' + ROMAN + r' ', r'\1号突撃砲 '),
	(r'^Marder ' + ROMAN + r' ([A-Z])$', r'マルダー\1 \2型'),
	(r'^Marder ', 'マルダー'),
	(r'^Grille Ausf\. ([A-Z])', r'グリレ\1型'),
	(r'^Hummel', 'フンメル'), (r'^Wespe', 'ヴェスペ'), (r'^Nashorn', 'ナースホルン'),
	(r'^PSW ', 'Sd.Kfz.'), (r'^SPW ', 'Sd.Kfz.'), (r'^Sd\. Kfz\. ', 'Sd.Kfz.'),
	(r'Wurfrahmen', 'ロケット発射機'), (r'^Panzerwerfer 42', 'パンツァーヴェルファー42'), (r'^Reihenwerfer', 'ライエンヴェルファー'),
	(r'^Munitionsschlepper', '弾薬運搬車'), (r'^Munitionspanzer', '弾薬運搬戦車'),
	(r'Opel Blitz', 'オペル・ブリッツ'), (r'Kubelwagen', 'キューベルワーゲン'), (r'Horch', 'ホルヒ'),
	(r'Mercedes-Benz', 'メルセデス・ベンツ'), (r'Steyr', 'シュタイア'), (r'Buessing-NAG', 'ビュッシング-NAG'),
	(r'Krupp[- ]Protze', 'クルップ・プロッツェ'), (r'Borgward', 'ボルクヴァルト'), (r'Henschel', 'ヘンシェル'),
	(r'Tempo Vidal', 'テンポ・ビダル'), (r'Einheitsdiesel', '統制型ディーゼル'), (r'Hansa-Lloyd', 'ハンザ・ロイド'),
	# アメリカ
	(r'Sherman', 'シャーマン'), (r'Stuart', 'スチュアート'), (r'\bLee\b', 'リー'), (r'\bGrant\b', 'グラント'),
	(r'Chaffee', 'チャーフィー'), (r'Pershing', 'パーシング'), (r'Wolverine', 'ウルヴァリン'), (r'Hellcat', 'ヘルキャット'),
	(r'Jackson', 'ジャクソン'), (r'Priest', 'プリースト'), (r'Greyhound', 'グレイハウンド'), (r'Calliope', 'カリオペ'),
	(r'Crocodile', 'クロコダイル'), (r'Achilles', 'アキリーズ'), (r'Kangaroo', 'カンガルー'), (r'Satan', 'サタン'),
	(r'Scout Car', '偵察車'), (r'half-track', 'ハーフトラック'), (r'Light Tractor', '軽牽引車'), (r'Medium Tractor', '中牽引車'),
	(r'Heavy Tractor', '重牽引車'), (r'Prime Mover', '牽引車'), (r'\bHST\b', '高速牽引車'), (r'Dodge', 'ダッジ'),
	(r'Chevrolet', 'シボレー'), (r'Studebaker', 'スチュードベーカー'), (r'Diamond T', 'ダイヤモンドT'), (r'\bFord\b', 'フォード'),
	(r'Mack', 'マック'), (r'GMC CCKW 2\.5 ton truck', 'GMC CCKW 2.5トン・トラック'), (r'GMC DUKW', 'GMC ダック'),
	(r'(\d)/(\d)-ton Truck', r'\1/\2トン・トラック'), (r'(\d)/(\d)-ton', r'\1/\2トン'), (r'Truck', 'トラック'),
	# イギリス
	(r'Crusader', 'クルセーダー'), (r'Matilda', 'マチルダ'), (r'Valentine', 'バレンタイン'), (r'Cromwell', 'クロムウェル'),
	(r'Challenger', 'チャレンジャー'), (r'^Comet', 'コメット'), (r'Churchill', 'チャーチル'), (r'Cruiser Mk', '巡航戦車Mk.'),
	(r'^A(9|10|13) ', r'A\1 '), (r'Bishop', 'ビショップ'), (r'Deacon', 'ディーコン'), (r'^Archer', 'アーチャー'),
	(r'Humber', 'ハンバー'), (r'Staghound', 'スタッグハウンド'), (r'Marmon-Herrington', 'マーモン・ヘリントン'),
	(r'Bren Gun Carrier', 'ブレンガン・キャリア'), (r'Loyd Carrier', 'ロイド・キャリア'), (r'AT Rifle Carrier', '対戦車ライフル・キャリア'),
	(r'MG Carrier', '機関銃キャリア'), (r'2-Inch Carrier', '2インチ迫撃砲キャリア'), (r'FTR Carrier Mk\. II', 'ワスプ火炎放射キャリア'),
	(r'(\d) Pdr Portee', r'\1ポンド砲ポーティー'), (r'Portee', 'ポーティー'), (r'Frog', 'フロッグ'),
	(r'Bedford', 'ベッドフォード'), (r'Morris', 'モーリス'), (r'AEC Matador', 'AEC マタドール'), (r'Scammell Pioneer', 'スキャメル・パイオニア'),
	(r'Leyland Retriever', 'レイランド・リトリーバー'), (r'Thornycroft Tartar', 'ソーニクロフト・タータ'), (r'Carden-Loyd', 'カーデン・ロイド'),
	(r'Vickers', 'ヴィッカース'), (r'Bofors', 'ボフォース'), (r'AA Gun', '対空砲'), (r'(?<= )AA\b', '対空型'),
	# ソ連
	(r'^(T-\d+[A-Z]?|BT-\d|OT-\d+|KV-\d|T-34-\d+|OT-34-\d+|OT-34) M(\d\d)(/\d\d)?', lambda m: m.group(1) + ' 19' + m.group(2) + (('/' + m.group(3)[1:]) if m.group(3) else '') + '年型'),
	(r'Komsomolets', 'コムソモーレツ'), (r'Vezdestoi', 'ヴェズジェホート'), (r'\bAPC\b', '装甲兵員輸送車'),
	# 共通
	(r'Light Tank', '軽戦車'), (r'Armoured Car', '装甲車'),
]

SUFFIX = {
	'early': '初期型', 'Early': '初期型', 'late': '後期型', 'Late': '後期型',
	'POL': 'ポーランド軍', 'FIN': 'フィンランド軍', 'ROM': 'ルーマニア軍', 'HUN': 'ハンガリー軍', 'ITA': 'イタリア軍',
	'USSR': 'ソ連軍', 'UK': 'イギリス軍', 'GER': 'ドイツ軍', 'JP': '日本軍', 'ROC': '中華民国軍', 'BEL': 'ベルギー軍',
	'MG': '機関銃型', 'half-track': 'ハーフトラック型', '6 rad': '6輪', '8 rad': '8輪', 'A': 'A',
}

NICK = {
	'Flamingo': 'フラミンゴ', 'Luchs': 'ルクス', 'Panther': 'パンター', 'Tiger P': 'ティーガー(P)', 'Tiger': 'ティーガー',
	'King Tiger': 'ケーニヒスティーガー', 'Bison': 'ビゾン', 'Brummbaer': 'ブルムベア', 'Elefant': 'エレファント', 'Bufla': 'ブーフラ',
	'Hetzer': 'ヘッツァー', 'Pakwagen': 'パックワーゲン', 'Ente': 'エンテ', 'Jagdpanther': 'ヤークトパンター', 'Jagdtiger': 'ヤークトティーガー',
	'Sturer Emil': 'シュトゥーラー・エミール', 'Sturmtiger': 'シュトゥルムティーガー', 'Rollender Sarg Ost': 'ローレンダー・ザルク・オスト',
	'Puma': 'プーマ', 'Stummel': 'シュトゥンメル', 'Stuka zu Fub': '歩くシュトゥーカ', 'Kubelwagen': 'キューベルワーゲン',
	'Pantera': 'パンテラ', 'Tigr': 'ティグル', 'Art-Shturm': 'アルト・シュトゥルム', 'Sturmi': 'シュトゥルミ', 'Kettenkrad': 'ケッテンクラート',
	'Famo': 'ファモ', 'Schwimmwagen': 'シュビムワーゲン', 'Maultier': 'マウルティア', 'Zippo': 'ジッポー', 'Jumbo': 'ジャンボ',
	'Scott': 'スコット', 'Water Buffalo': 'ウォーター・バッファロー', 'Amtrack': 'アムトラック', 'Amtank': 'アムタンク',
	'Meat Chopper': 'ミートチョッパー', 'Jeep': 'ジープ', 'Jimmy': 'ジミー', 'Beep': 'ビープ', 'Seep': 'シープ', 'Duck': 'ダック',
	'Lince': 'リンチェ', 'Tetrarkh': 'テトラルフ', 'Valya-Tanya': 'ヴァーリャ・ターニャ', 'Wasp': 'ワスプ', 'Firefly': 'ファイアフライ',
	'Oke': 'オーク', 'Dingo': 'ディンゴ', 'Tatanagar': 'タタナガール', 'Dorchester': 'ドーチェスター', 'Yonki': 'くろがね四起',
	'Suchka': 'スーチカ', 'Zveroboy': 'ズヴェロボーイ', 'Katyusha': 'カチューシャ', 'Kozlik': 'コズリク', 'Stalinets': 'スターリネッツ',
	'Vezdestoi': 'ヴェズジェホート', 'Emka': 'エムカ', 'Polundra': 'ポルンドラ', 'Zakhar': 'ザハール',
}


def translate(name):
	m = re.match(r'^(.*?) \(([^()]+)\)$', name)
	base, suf = (m.group(1), m.group(2)) if m else (name, None)
	# 末尾の括弧が2つあるもの（Panzer VIe (Late)）や (r)(f) は base 側に残る
	out = JAPAN.get(base) or SINGLE.get(base)
	if out is None:
		out = base
		for pat, rep in RULES:
			out = re.sub(pat, rep, out)
		if out == base and (suf is None or suf not in SUFFIX):
			return None
	if suf is not None:
		out += '（%s）' % SUFFIX.get(suf, suf)
	return out


def main():
	d = json.load(open(os.path.join(GAME, 'data', 'unit_type_defs.json'), encoding='utf8'))
	names, miss = {}, []
	for k, v in d.items():
		if v.get('origin_nation') not in NATIONS or v.get('category') != 'Vehicle':
			continue
		ja = translate(k)
		if ja:
			names[k] = ja
		else:
			miss.append(k)
		nick = v.get('nick_name')
		if nick and nick in NICK:
			names[nick] = NICK[nick]
	json.dump(names, open(os.path.join(ROOT, 'tr', 'units_names.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
	print('訳した', len(names), '英語のまま', len(miss))
	print(' | '.join(miss))


if __name__ == '__main__':
	main()
