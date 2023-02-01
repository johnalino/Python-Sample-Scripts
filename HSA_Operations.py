# coding=utf-8
import os, sys, csv, json, subprocess, traceback
from glob import glob
from time import strftime
from datetime import date, timedelta
from Operations import *

def decrypt_PGP(src, dest, passphrase=None):
	if passphrase: subprocess.call('C:\Program Files (x86)\PGP Corporation\PGP Command Line\pgp.exe --decrypt "{}" --output {} --passphrase {}'.format(src, dest, passphrase))
	else: subprocess.call('C:\Program Files (x86)\PGP Corporation\PGP Command Line\pgp.exe --decrypt "{}" --output {}'.format(src, dest))

def encrypt_to_HSA():
	subprocess.call('pgp.exe -e -r "PES2" -r "Valid HSA" {}*. --input-cleanup wipe --output {}'.format(Dirs.stage, Dirs.secure+'SecureData\\'))

def move_to_hold():
	files = (glob(Dirs.raw_files+'*')+
			 glob(Dirs.reports+'*.*')+
			 glob(Dirs.backup+'*')+
			 glob(Dirs.dumps+'*')+
			 glob(Dirs.inventory+'*')+
			 glob(Dirs.labels+'*')+
			 glob(Dirs.pdf+'*.pdf')+
			 glob(Dirs.warehouse+'*')+
			 glob(Dirs.datadumps+'*')+
			 glob(Dirs.return_files+'*')+
			 glob(Dirs.stage+'*'))
	for f in files:
		move_file(f, Dirs.hold)

def print_pages(print_whs=False, print_pdf=True, delete_pdf=True):
	if print_whs:
		for each_whs in glob(Dirs.warehouse+'*.whs'):
			subprocess.call('C:\\Program Files (x86)\\Textpad 5\\Textpad.exe -p {} "HP Laserjet 4250 (Visa)"'.format(each_whs))

	if print_pdf:
		for pdf in glob(Dirs.pdf+'*.pdf'):
			subprocess.call(Dirs.programs+'PDF_Printer\\PDFtoPrinter.exe "{}" "{}"'.format(pdf, 'Kyocera TASKalfa 406ci KX'))
			if delete_pdf: os.remove(pdf)
			else: move_file(pdf, Dirs.default)

def sla_date(days=2):
	# need to update this every year
	holidays = ['12/24/19','12/25/19','12/31/19','01/01/20','05/25/20','07/03/20','09/07/20','11/26/20','11/27/20','12/24/20','12/25/20','12/31/20']
	
	ship_date = date.today()

	for day in range(days):
		ship_date += timedelta(days=1)

		while ship_date.weekday() in (5, 6) or ship_date.strftime('%m/%d/%y') in holidays:
			ship_date += timedelta(days=1)

	return ship_date.strftime('%m/%d/%y')

def error(message='',error_filename=''):
	print 'An error was found.\n\n'+traceback.format_exc()
	with open(Dirs.error+strftime('Program_%m%d%Y_%I%M%S.error'),'w') as error_file:
		error_file.write('{}\n\n{}\n'.format(message, traceback.format_exc()))

	try: 
		with open(Dirs.reports_sftp+error_filename+'-error.txt','w') as fxp: fxp.write(message) ##pass #
	except: pass 

	sys.exit()

def check_directories_and_files():
	directories = [Dirs.default, Dirs.hold, Dirs.raw_files, Dirs.src_files, Dirs.references, Dirs.stage, Dirs.reports, Dirs.pdf, Dirs.dumps, Dirs.error, Dirs.labels, Dirs.backup,
		Dirs.datadumps, Dirs.inventory, Dirs.warehouse, Dirs.return_files, Dirs.az_line, Dirs.programs, Dirs.card_scans, Dirs.gift, Dirs.secure, Dirs.pdf+'hold\\', Dirs.reports_sftp,
		Dirs.reports_sftp+'Daily\\','O:\\dumps\\','O:\\Daily Reports\\','R:\\']
	files = ['ReleaseSheetTemplate.pdf','ShipDetailTemplate.pdf','HSA_Config.json','fields.json','HSA_Database.sqlite']
	for d in directories:
		if not os.path.isdir(d):
			print 'This directory couldn\'t be found (not mapped): '+d
			return False
	for f in files:
		if not os.path.isfile(Dirs.references+f):
			print 'This file couldn\'t be found: '+f
			return False
	return True

def check_json(json_file):
	try:
		data = json.load(open(json_file, 'r'))
	except:
		print traceback.format_exc()
	else:
		print json_file+' - is good.'

def bad_csv(raw_file, required_fields):
	with open(raw_file,'r') as file_read: file_data = csv.DictReader(file_read.readlines())

	file_fieldnames = [fieldname.lower() for fieldname in file_data.fieldnames]
	for field in required_fields:
		if field.lower() not in file_fieldnames:
			print 'Missing field: ' + field
			return True

	return False

def bad_txt_file(raw_file, ignore_header=False, ignore_footer=False, min_chars=None, delimiter=None, min_delimiters=None):
	if (min_chars==None and delimiter==None and min_delimiters==None) or (delimiter==None and not min_delimiters) or (min_delimiters==None and not delimiter):
		print 'Invalid parameter inputs: min_chars={}, delimiter={}, min_delimiters={}\n'.format(min_chars, delimiter, min_delimiters)
		return

	with open(raw_file,'r') as file_read: file_data = file_read.readlines()

	if ignore_header: del file_data[0]
	if ignore_footer: del file_data[-1]

	# All lines have to be at least a specific length
	if min_chars is not None:
		for line in file_data:
			if len(line) < min_chars:
				print '{} has {:,} characters. Minimum is {:,}\n'.format(os.path.basename(raw_file), len(line), min_chars)
				return True

	# All lines need to contain this many iterations of a delimiter
	if (delimiter is not None) and (min_delimiters is not None):
		for line in file_data:
			if len(line.split(delimiter)) < min_delimiters:
				print '{} has {:,} delimiters. Minimum is {:,}\n'.format(os.path.basename(raw_file), len(line.split(delimiter)), min_delimiters)
				return True

	return False

def carrier_address(record, *address_lines):
	lines = [record[line] for line in address_lines if record[line].strip()]
	for remaining in range(len(address_lines) - len(lines)): lines.append('')

	for line, address_line in enumerate(address_lines): record[address_line] = lines[line]

def combine(*fields, **delimiter):
	return delimiter.get('delimiter', ' ').join(f for f in fields if f.strip())

def exp(raw_exp, e1_start=0, e1_end=2, e2_start=2, e2_end=4):
	return raw_exp[e1_start:e1_end] + '/' + raw_exp[e2_start:e2_end]

acctmasked = lambda acct: acct[:4]+' '+acct[4:6]+'XX XXXX '+acct[12:16]
phone_number = lambda p: (p[:3]+'-'+p[3:6]+'-'+p[6:10]).rstrip('-')
zip_code = lambda z: (z[:5]+'-'+z[5:9]).rstrip('-')

if __name__ in '__main__':
	pass
