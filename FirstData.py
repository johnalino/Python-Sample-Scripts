from NSA import *

layouts = {
	'General1': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General2': '{seq:0>6}|D01|{acct4444}||D02|{upc}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General3': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|{acct}||D03|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General4': '{seq:0>6}|D01|{acct4444}||BD1|{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General5': '{seq:0>6}|D01|{acct4444}||D02|{pin}||D03|CARD#||D04|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General6': '{seq:0>6}|D01|{acct4444}||D02|{pin}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General7': '{seq:0>6}|D01|{acct4444}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General8': '{seq:0>6}|D01|{acct4444}||BD1|{acct}||D02|CARD#:||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General9': '{seq:0>6}|D01|{acct4444}||D02|CARD#:||D03|{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'General10': '{seq:0>6}|D01|91 111 {acct}||BD1|91111{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'Walmart1': '{seq:0>7}|D01|{acct4444}||D02|{pin}||BD1|{barc}||D03|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'Walmart2': '{seq:0>7}|D01|{acct4444}||D02|{pin}||BD1|{upc:.11}{acct:0>19}||D03|{upc:.11}||D04|{seq:0>7}||D05|PIN#||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'Walmart3': '{seq:0>7}|D01|{acct4444}||D02|{pin}||BD1|{barc}||D03|{seq:0>7}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'TueMorn1': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|TUESDAYMORN/VALUELINK{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'TueMorn2': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|TUESDAYMORN/CELEB{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'TueMorn3': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|TUESDAYMORN/HOLID{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'TueMorn4': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|TUESDAYMORN/EVYDAY{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'TueMorn5': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|TUESDAYMORN/MERCH{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'BestBuy1': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|{acct}||D03|{seq:0>6}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'BestBuy2': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|{acct}||D03|{seq:0>6}||D04|INITIAL VALUE ${denom}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'SandF1': '{seq:0>6}|D01|91 111 {acct}||BD1|91111{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'Chopper1': '{seq:0>6}|D01|{acct4444}||BD1|{upc:.11}{acct}||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'Dolby1': '{seq:0>6}|D01|{acct4444}||D02|{pin}||D03|CARD#||D04|PIN#||D05|FD60605||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',

	'SKmart1': '{seq:0>6}|D01|{acct4444}||D02|{pin}||BD1|072000150870||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n',
	'SKmart2': '{seq:0>6}|D01|{acct4444}||D02|{pin}||D03|ACCT#:||BD1|D79 76023||D15|MD( ) BE({BE})||D16|{tm}||M1|%{track1}?||M2|;{track2}?|\n'
}

jobname = 'Sterling' # Name of Client
testing = True #False # false = write test/prod files to GIFT, make approval and datadump in files; true = output files in current working dir

files = [
	{'raw_file':     'mf368387_20210607_001.out',
	'layout':        'General1',
	'tick_marks':    100,    # See Work Order
	'test_quantity': 0,    # See Packing Slip
	'denom':         '',
	'upc':           '' }, # If no UPC, leave blank

	{'raw_file':     'mf368388_20210607_001.out',
	'layout':        'General1',
	'tick_marks':    100,    # See Work Order
	'test_quantity': 0,    # See Packing Slip
	'denom':         '',
	'upc':           '' }, # If no UPC, leave blank

	{'raw_file':     '',
	'layout':        '',
	'tick_marks':    0,    # See Work Order
	'test_quantity': 0,    # See Packing Slip
	'denom':         '',
	'upc':           '' }, # If no UPC, leave blank

	{'raw_file':     '',
	'layout':        '',
	'tick_marks':    0,    # See Work Order
	'test_quantity': 0,    # See Packing Slip
	'denom':         '',
	'upc':           '' }, # If no UPC, leave blank

	{'raw_file':     '',
	'layout':        '',
	'tick_marks':    0,    # See Work Order
	'test_quantity': 0,    # See Packing Slip
	'denom':         '',
	'upc':           '' } # If no UPC, leave blank
]

def main():
	dump = Datadump(jobname=jobname)
	batch = 250 if 'walmart' in jobname.lower() else 500

	for f in files:
		if not f['raw_file']: continue

		# Create FirstData instance; process data, set up test data, make_approval, set up layout
		fd = FirstData(f['raw_file'], testing)
		fd.process_data(upc=f['upc'], denom=f['denom']) # parse to dic 
		fd.test_data = get_test_records(fd.prod_data, f['test_quantity']) ## for not reuse test records in production file again
		#fd.test_data = get_test_records(fd.prod_data, f['test_quantity'], run_twice=True) ## use test records in production file again
		fd.make_approval()
		layout = layouts[f['layout']]

		# Test data - write test file, add to Datadump
		if fd.test_data:
			filename_test = fd.base_filename + 'Test.txt'
			process_file(filename_test, layout, fd.test_data, batch, f['tick_marks'])  ## write to machine file
			dump.add_file(raw_file=fd.raw_file, processed_file=filename_test, batch=batch, tm=f['tick_marks'])

		if fd.prod_data:
			filename_prod = fd.base_filename + 'Prod.txt'
			process_file(filename_prod, layout, fd.prod_data, batch, f['tick_marks'])
			dump.add_file(raw_file=fd.raw_file, processed_file=filename_prod, batch=batch, tm=f['tick_marks'])

	dump.finish(('' if testing else Dirs.default)+strftime('FD_{}_%m%d.txt'.format(jobname)))

if __name__ in '__main__':
	import traceback
	try: main()
	except: print traceback.format_exc()
