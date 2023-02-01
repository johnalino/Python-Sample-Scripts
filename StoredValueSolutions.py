from NSA import *

layouts = {
	'General1': '{seq:0>6}|D01|{acct}||D02|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General2': '{seq:0>6}|D01|{acct}||D02|{acct44443}||D03|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General3': '{seq:0>6}|D01|{acct}||D02|{acct44443}||D03|{pin}||D15|MD( ) BE({BE})||D16|{tm}|\n',
	'General4': '{seq:0>6}|D01|{acct}||D02|{pin}||D03|CARD #||D04|PIN #||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General5': '{seq:0>6}|BD1|{acct}||D01|{acct44443}||D02|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General6': '{seq:0>6}|D01|{acct}||D02|{acct44443}||D03|{pin}||BD1|{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General7': '{seq:0>6}|D01|{acct}||D02|{acct44443}||BD1|{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General8': '{seq:0>6}|D01|{acct}||D02|{acct44443}||D03|{pin}||BD1|{barc_ssc}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General9': '{seq:0>6}|D01|{acct}||D02|{acct34444}||D03|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'General0': '{seq:0>6}|D01|{acct}||D02|{pin}||D03|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',

	'QR_Code1': '{seq:0>6}|D01|{acct}||D02|{acct44443}||D03|{pin}||BD1|{url}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'QR_Code2': '{seq:0>6}|BD1|{acct}||D01|{acct44443}||D02|{pin}||BD2|{url}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'QR_Code3': '{seq:0>6}|BD1|{acct}||D01|{acct44443}||D02|{pin}||BD2|{url}||D03|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'QR_Code0': '{seq:0>6}|BD1|{acct}||D01|{acct44443}||D02|{pin}||BD2|{url}||D03|PIN#||D04|Client Code RUEGC||D05|Date 09/19 ALL||D06|Description DEV||D07|Barcode Test||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',

	'Pappas1' : '{seq:0>6}|D01|{acct}||D02|{acct18_1}||D03|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',

	'TJX1'    : '{seq:0>7}|D01|{acct}||D02|{acct6445}||D03|{pin}||D04|CARD #||D05|CSC:||D06|00053777||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
	'TJX2'    : '{seq:0>6}|D01|{acct}||D02|{acct6445}||D03|{pin}||D04|TARJETA #||D05|CSC:||D06|00054129||D15|MD( ) BE({BE})||D16|{tm}||M1|%{SVSStandardTrack1}?||M2|;{SVSStandardTrack2}?|\n',
}

jobname = 'Loblaws' # Name of Client -only show on dump.

testing = False

files = [
	{'raw_file': '1126813_BLK_L013_20200416_SSC.txt', 'layout': 'General8', 'tm': 0},
	{'raw_file': '1126814_BLK_L013_20200416_SSC.txt', 'layout': 'General8', 'tm': 0},
	{'raw_file': '', 'layout': '', 'tm': 0},
	{'raw_file': '', 'layout': '', 'tm': 0},
	{'raw_file': '', 'layout': '', 'tm': 0},
	{'raw_file': '', 'layout': '', 'tm': 0}
]

def main():
	dump = Datadump(jobname=jobname)
	BE = 250 if 'walmart' in jobname.lower() else 500  #batch end

	for f in files:
		if not f['raw_file']: continue
		svs = SVS(f['raw_file'], testing)
		if not svs.good_to_go: continue
		svs.process_data()
		filename = svs.base_filename[:-1]+'.txt'
		process_file(filename, layouts[f['layout']], svs.prod_data, BE, f['tm'])
		dump.add_file(raw_file=f['raw_file'], processed_file=filename, batch=BE, tm=f['tm'])

	dump.finish(('' if testing else Dirs.default)+strftime('SVS_{}_%m%d.txt'.format(jobname)))

if __name__ in '__main__':
	import traceback
	try: main()
	except: print traceback.format_exc()
