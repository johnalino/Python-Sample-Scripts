import os, shutil, subprocess
from os.path import basename, splitext
from time import strftime
from glob import glob
from Operations import *

# File Operations
def process_file(filename, layout, data, batch=500, tm=0, header=None, **extra_fields):
	print '{}: {:>10,}; batch={}, tick marks={}'.format(filename, len(data), batch, tm)
	if len(data) >= 1000000: print 'Warning: {} contains 1 million or more records. Make sure seq len is at least 7'.format(filename)
	tm = tm or (len(data)+1)

	with open(filename, 'w') as file_out:
		if header: file_out.write(header)
		for seq, record in enumerate(data, 1):
			record.update(extra_fields)

			for field in record:
				if ('{'+field+'}' in layout or '{'+field+':' in layout) and not record[field]:
					raise Exception(field+' found in layout, but was not in data!')

			file_out.write(layout.format(
				seq=seq,
				BE='1' if (seq%batch==0 or seq==len(data)) else '0',
				tm='--' if seq%tm==0 else '  ',
				**record))

def rewrite_file(filename, data, **file_args):
	batch = file_args.get('batch',500)
	tm = file_args.get('tm',0)
	seqlen = file_args.get('seqlen',6)
	filename = file_args.get('filename_overwrite') or filename
	print '{} - batch={}, tm={}, seqlen={}, len={}'.format(filename, batch, tm, seqlen, len(data))

	with open(filename,'w') as file_out:
		for seq, line in enumerate(data, 1):
			new_line = str(seq).zfill(seqlen) + line[seqlen:]

			new_line = new_line.replace('BE(0)','BE(1)') if seq%batch==0 or seq==len(data) else new_line.replace('BE(1)','BE(0)')
			if tm: new_line = new_line.replace('|D16|  ','|D16|--') if seq%tm==0 else new_line.replace('|D16|--','|D16|  ')
			file_out.write(new_line)

def file_combine(*files, **file_args):
	all_lines = []
	for each_file in files:
		with open(each_file,'r') as file_read:
			data = file_read.readlines()
			if not data[-1].endswith('\n'): data[-1] = data[-1] + '\n'
			all_lines.extend(data)

	rewrite_file(Dirs.programs+strftime('Combined_%m%d%y_%I%M%S.txt'), all_lines, **file_args)

def file_split(filename, *splits, **file_args):
	with open(filename,'r') as file_read: lines = file_read.readlines()
	if sum(splits) != len(lines): raise Exception('Unequal lengths! splits: {}, file: {}'.format(sum(splits), len(lines)))

	file_splits = []
	i, j = 0, 0
	for s in splits:
		i = j
		j = i + s
		file_splits.append(lines[i:j])

	for i, each_split in enumerate(file_splits, 1):
		rewrite_file(Dirs.programs+splitext(basename(filename))[0]+'-'+str(i)+'.txt', each_split, **file_args)

def file_reverse(filename, **file_args):
	with open(filename,'r') as file_read: lines = file_read.readlines()[::-1]
	if not lines[0].endswith('\n'): lines[0] = lines[0] + '\n'

	rewrite_file(Dirs.programs+splitext(basename(filename))[0]+'-rev.txt', lines, **file_args)

def file_renumber(filename, **file_args):
	with open(filename,'r') as file_read: lines = file_read.readlines()
	rewrite_file(Dirs.programs+basename(filename), lines, **file_args)

def file_split_generic(filename, has_header=False, has_footer=False, *splits):
	with open(filename,'r') as file_read: data = file_read.readlines()
	header = '' if not has_header else data.pop(0)
	footer = '' if not has_footer else data.pop()

	if sum(splits) != len(data): raise Exception('Unequal lenghts! splits: {}, file: {}'.format(sum(splits), len(data)))

	file_splits = []
	i, j = 0, 0
	for s in splits:
		i = j
		j = i + s
		file_splits.append(data[i:j])

	for k, each_split in enumerate(file_splits, 1):
		with open(Dirs.programs+splitext(basename(filename))[0]+'-'+str(k)+'.txt', 'w') as file_out:
			file_out.write(header)
			file_out.writelines(each_split)
			file_out.write(footer)

# Test Data Operations
def get_test_records(data, quantity=0, take_from_top=True, run_twice=False):
	test_data = []

	if not take_from_top:
		test_data = data[-quantity:]
		if not run_twice:
			del data[-quantity:]
	else:
		test_data = data[:quantity]
		if not run_twice:
			del data[:quantity]

	return test_data

def get_test_layout(old_layout, *test_fields):
	max_fieldnum = max([f for f in range(15) if '|D{:0>2}|'.format(f) in old_layout])
	if max_fieldnum+len(test_fields) > 14: raise Exception('Too many batters!')

	test_layout = ''.join(['||D{:0>2}|'.format(max_fieldnum+n) + '{'+field+'}' for n, field in enumerate(test_fields, 1)])
	return old_layout.split('||D15|')[0] + test_layout + '||D15|' + old_layout.split('||D15|')[1]

# Checkdigit Operations
def checkdigit(number):
	digits = [int(d) for d in str(number)]
	odd_digits  = digits[0::2]
	even_digits = digits[1::2]

	checksum = sum(even_digits)
	for d in odd_digits:
		checksum += (d * 2) % 10
		if d > 4:
			checksum += 1

	return str((10 - (checksum % 10)) % 10)

full_number = lambda n: str(n)+checkdigit(n)

def checkdigit_upc(upc):
	digits = [int(i) for i in str(upc)]
	odd_digits = digits[0::2]

	checksum = sum(digits[1::2])
	for odd_digit in odd_digits:
		checksum += (odd_digit * 3)

	return str((10 - (checksum % 10)) % 10)

full_upc = lambda u: str(u) + checkdigit_upc(u)

# Condition/Value Checking Operations
def check_barcode(barcode, barc_len=30):
	if len(barcode) != barc_len:
		raise Exception('Warning: barcode length is not {}. barcode={}'.format(barc_len, barcode))

def check_denom(denom, static_denom):
	if denom!='00000' and static_denom!='$VGC':
		if denom.lstrip('0')[:-2] != static_denom[1:]:
			raise Exception('Unequal denom values! denom={}; static_denom={}'.format(denom, static_denom))

def check_encoding_bhn(track1, upc, denom):
	if track1.split('^')[1].split('$')[0][:11] != upc[:11]:
		raise Exception('Unequal upc values! track1={}; upc={}'.format(track1.split('^')[1].split('$')[0][:11], upc[:11]))
	if track1.split('$')[1] != denom:
		raise Exception('Unequal denom values! track1={}; denom={}'.format(track1.split('$')[1], denom))

def check_encoding(track1, track2):
	if track1[0]!='%' or track1[-1]!='?':
		print 'Check track1 start/end sentinels.'
	if track2[0]!=';' or track2[-1]!='?':
		print 'Check track2 start/end sentinels.'

	if len(track1) > 79:
		print 'Track1 length = ' + str(len(track1))
	if len(track2) > 40:
		print 'Track2 length = ' + str(len(track2))

def track1_formatting(track1):
	if not track1.startswith('%'):
		track1 = '%' + track1
	if not track1.endswith('?'):
		track1 = track1 + '?'
	return track1

def track2_formatting(track2):
	if not track2.startswith(';'):
		track2 = ';' + track2
	if not track2.endswith('?'):
		track2 = track2 + '?'
	return track2

if __name__ in '__main__':
	pass
