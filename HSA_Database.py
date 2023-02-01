import os, time, copy, json, subprocess, xlsxwriter, sqlite3
from collections import OrderedDict
from os.path import splitext, basename
from HSA_Operations import *

# sebastianraschka.com/articles/2014_sqlite_in_python_tutorial.html
database_HSA = Dirs.references+'HSA_Database.sqlite'
database_duplicates = Dirs.references+'Duplicates.sqlite'

def add_to_database(report_setup):
	if not os.path.isfile(database_HSA) or not os.path.isfile(database_duplicates):
		raise Exception('Cannot find either HSA_Database.sqlite or Duplicates.sqlite\nExiting program.')

	conn = sqlite3.connect(database_HSA)
	c = conn.cursor()

	# try -insert new filename; except -insert old filename to Duplicates.sqlite; finally -update old filename in HSA_Database.sqlite to new filename
	try:
		c.execute('INSERT INTO files (filename) VALUES ("{filename}")'.format(**report_setup.fields))
		print report_setup.fields['filename'] + ' added to database, fam.'
	except sqlite3.IntegrityError:
		print '{filename} already exists. Original data moved to Duplicates.sqlite, {filename} will be updated.'.format(**report_setup.fields)
		conn_dupe = sqlite3.connect(database_duplicates)
		c_dupe = conn_dupe.cursor()

		c.execute('SELECT * FROM files')
		descriptions = [d[0] for d in c.description]
		c.execute('SELECT * FROM files WHERE filename="{filename}"'.format(**report_setup.fields))
		file_data = c.fetchall()[0]

		c_dupe.execute('INSERT INTO files (filename) VALUES ("temporary filename placeholder")')
		for row in zip(descriptions, file_data)[1:]:
			c_dupe.execute('UPDATE files SET {}="{}" WHERE filename="temporary filename placeholder"'.format(row[0], row[1]))
		c_dupe.execute('UPDATE files SET filename="{}" WHERE filename="temporary filename placeholder"'.format(file_data[0]))

		conn_dupe.commit()
		conn_dupe.close()
	finally:
		for field in report_setup.fields:
			try:
				c.execute('UPDATE files SET {field}="{field_value}" WHERE filename="{filename}"'.format(field=field, field_value=report_setup.fields[field], **report_setup.fields))
			except:
				print 'Warning: no column for ' + field

	conn.commit()
	conn.close()

def add_column():
	fieldname = ''

	# Add column to HSA_Database.sqlite
	conn = sqlite3.connect(database_HSA)
	c = conn.cursor()

	c.execute('ALTER TABLE files ADD COLUMN {} TEXT DEFAULT ""'.format(fieldname))

	c.commit()
	c.close()

	# Add column to Duplicates.sqlite
	conn_dupe = sqlite3.connect(database_duplicates)
	c_dupe = conn_dupe.cursor()

	c_dupe.execute('ALTER TABLE files ADD COLUMN {} TEXT DEFAULT ""'.format(fieldname))

	c_dupe.commit()
	c_dupe.close()

def show_database_rows(database_filename):
	wb = xlsxwriter.Workbook(Dirs.programs+'{}.xlsx'.format(splitext(basename(database_filename))[0]))
	conn = sqlite3.connect(database_filename)
	c = conn.cursor()

	c.execute('SELECT name FROM sqlite_master WHERE type="table"')
	for table in [t[0] for t in c.fetchall()]:
		c.execute('SELECT * FROM {}'.format(table))
		descriptions = [d[0] for d in c.description]
		all_rows = c.fetchall()

		sh = wb.add_worksheet(table)
		for d, desc in enumerate(descriptions):
			sh.write(0, d, desc)
		for r, row in enumerate(all_rows, 1):
			for c, value in enumerate(row):
				sh.write(r, c, value)

	conn.commit()
	conn.close()

def create_database():
	## Delete table
	#c.execute('drop table if exists files')

	fields = json.load(open(Dirs.references+'blank_fields.json'), object_pairs_hook=OrderedDict)['fields']

	def add_columns(cursor, fields):
		for field in fields:
			if field != 'filename':
				cursor.execute('ALTER TABLE files ADD COLUMN {} TEXT DEFAULT ""'.format(field))

	# HSA_Database.sqlite
	conn = sqlite3.connect(database_HSA)
	c = conn.cursor()
	
	# Create table with one column of unique values
	c.execute('CREATE TABLE files (filename TEXT PRIMARY KEY)')

	# Create columns for table
	add_columns(c, fields)

	conn.commit()
	conn.close()

	# Duplicates.sqlite
	conn_dupe = sqlite3.connect(database_duplicates)
	c_dupe = conn_dupe.cursor()

	# Create table with one column of repeatable values
	c_dupe.execute('CREATE TABLE files (filename TEXT)')

	# Create columns for table
	add_columns(c_dupe, fields)

	conn_dupe.commit()
	conn_dupe.close()

if __name__ in '__main__':
	#create_database()

	show_database_rows(database_HSA)
	show_database_rows(database_duplicates)

	#reprint_RS('TST021418')
