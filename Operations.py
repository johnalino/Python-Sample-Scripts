# coding=utf-8
import os, shutil, subprocess
from glob import glob
from time import strftime
from os.path import basename, splitext

class Dirs:
	programs     = 'C:\\Python27\\Programs\\'

	default_old  = 'D:\\Files\\'
	default      = 'D:\\Files2\\'
	hold         = 'D:\\Files2\\Hold\\'
	raw_files    = 'D:\\Files2\\Raw_Files\\'
	src_files    = 'D:\\Files2\\Src_Files\\'
	references   = 'D:\\Files2\\References\\'

	stage        = 'D:\\Files2\\Stage\\'
	reports      = 'D:\\Files2\\Reports\\'
	pdf          = 'D:\\Files2\\Reports\\Pdfs\\'
	dumps        = 'D:\\Files2\\Reports\\Dumps\\'
	error        = 'D:\\Files2\\Reports\\Error\\'
	labels       = 'D:\\Files2\\Reports\\Labels\\'
	backup       = 'D:\\Files2\\Reports\\Backup\\'
	datadumps    = 'D:\\Files2\\Reports\\Datadumps\\'
	inventory    = 'D:\\Files2\\Reports\\Inventory\\'
	warehouse    = 'D:\\Files2\\Reports\\Warehouse\\'
	return_files = 'D:\\Files2\\Reports\\Return_Files\\'

	az_line      = 'D:\\files2\\To_AZ\\'
	card_scans   = 'O:\\Card Scans\\'
	gift         = 'X:\\'
	secure       = '\\\\192.168.3.7\\Secure\\'
	reports_sftp = 'P:\\Reports\\'


# File Operations
def copy_file(src, dest, new_filename=None):
	if new_filename: shutil.copy2(src, dest+os.path.basename(new_filename))
	else: shutil.copy2(src, dest)

def move_file(src, dest, new_filename=None):
	if new_filename:
		if os.path.isfile(dest+os.path.basename(new_filename)): os.remove(dest+os.path.basename(new_filename))
		shutil.move(src, dest+os.path.basename(new_filename))
	else:
		if os.path.isfile(dest+os.path.basename(src)): os.remove(dest+os.path.basename(src))
		shutil.move(src, dest)


# Label Operations
def start_labels():
	if glob(Dirs.labels+'*.xlsx'): print 'Files detected in Labels folder. Moving them to hold folder.'
	for label_file in glob(Dirs.labels+'*.xlsx'): move_file(label_file, Dirs.hold)

def finish_labels(out_filename):
	subprocess.call('C:\\Program Files\\7-Zip\\7z.exe a "{}" {}*.xlsx'.format(out_filename, Dirs.labels))
	#subprocess.call('C:\\Program Files\\7-Zip\\7z.exe a C:\\Python27\\Programs\\test.zip C:\\Python27\\Programs\\*.pin -p"password"') # zip with password
	#subprocess.call('"C:\\Program Files\\7-Zip\\7z.exe" x "C:\\Python27\\Programs\\test.zip" -p"password"') # extract with password
	#subprocess.call('"C:\\Program Files\\7-Zip\\7z.exe" x "C:\\Python27\\Programs\\test.zip" -o"D:\\Files\\Stage\\" -p"password"') # extract to folder with password

	for label_file in glob(Dirs.labels+'*.xlsx'): os.remove(label_file)


# Data Operations
def insert_char(string, *indexes, **char):
	if len(string) != sum(indexes):
		raise Exception('Indexes don\'t add up to length of string!\nindexes: {}, string: {}\n'.format(sum(indexes), len(string)))

	new_string = []
	i, j = 0, 0
	for index in indexes:
		i = j
		j = i + index
		new_string.append(string[i:j])

	return char.get('char',' ').join(new_string)

def split_data(data, split_qty):
	return [data[i:i+split_qty] for i in xrange(0, len(data), split_qty)]

def combine_files(new_filename, has_header=False, has_footer=False, delete_files=False, *files_to_combine):
	lines = []
	header = ''
	footer = ''
	for f in files_to_combine:
		with open(f,'r') as fr: data = fr.readlines()
		if has_header: header = data.pop(0)
		if has_footer: footer = data.pop()
		lines.extend(data)
		if delete_files: os.remove(f)
	with open(new_filename,'w') as fw:
		if has_header: fw.write(header)
		fw.writelines(lines)
		if has_footer: fw.write(footer)

if __name__ in '__main__':
	pass
