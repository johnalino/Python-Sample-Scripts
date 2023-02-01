# coding=utf-8
import re, copy, json, xlsxwriter, PDF_Reports, HSA_Database
from HSA_Operations import *

# Basic text file class
class TextFile:
	def __init__(self, out_filename):
		self.out_filename = out_filename
		self.data = []

	def add_line(self, line): self.data.append(line)

	def finish(self):
		with open(self.out_filename,'w') as output: output.writelines(self.data)

# Basic excel file class
class ExcelFile:
	def __init__(self, out_filename, sheetname='Sheet 1'):
		self.out_filename = out_filename
		self.sheetname = sheetname
		self.data = [] # Will be a list of lists, user is responsible for filling up data themselves

	def finish(self, bold_headers=False):
		self.output = xlsxwriter.Workbook(self.out_filename)
		self.sheet = self.output.add_worksheet(self.sheetname)
		if bold_headers: self.bold = self.output.add_format({'bold': True})

		for r, row in enumerate(self.data):
			for c, value in enumerate(row):
				if r==0 and bold_headers:
					self.sheet.write(r, c, value, self.bold) #write is build in funtion for xlsxwriter;
				else:
					self.sheet.write(r, c, value)
		self.output.close()


# Reports
class Backup(TextFile):
	bu_layout = '{gcsno}|{jobname}|{cust}|{qty}|{car}|{bin}|{intradate}|{mail}|{cardcode}|{label}|{encoding}|{ultrafront}|{color_uf}|{ultraback}|{color_ub}|{emboss}|{color_e}|{indentfrt}|{color_if}|{indentbck}|{color_ib}|{ultraform}|{carrier}|{filename}|{jobsetup}|{bulk}|{m1}|{m2}|{m3}|{m4}|{m5}|{envelope}|{insert1}|{insert2}|{insert3}|{insert4}|{insert5}|{insert6}|{prg}|{pt}|{scanm}|{spclmsg1}|{spclmsg2}|{ship}|{x3full}|{addcol1}|{addcol2}|{addcol3}|{addcol4}|{addcol5}|{shipdate}|{custfile}|{csr}|{barnesqc}\n'

	def add_document(self, report_config): self.data.append(Backup.bu_layout.format(**report_config.fields))

	def finish(self):
		if self.data: TextFile.finish(self)

class X3(TextFile):
	x3_layout = '"{jobname}"|"{CCode}"|"{qty}"|"{car}"|"{bin}"|"{intradate}"|"{mail}"|"{cardcode}"|"{label}"|"{encoding}"|"{ultrafront}"|"{color_uf}"|"{ultraback}"|"{color_ub}"|"{emboss}"|"{color_e}"|"{indentfrt}"|"{color_if}"|"{indentbck}"|"{color_ib}"|"{ultraform}"|"{carrier}"|"{filename}"|"{jobsetup}"|"{bulk}"|"{m1}"|"{m2}"|"{m3}"|"{m4}"|"{m5}"|"{envelope}"|"{insert1}"|"{insert2}"|"{insert3}"|"{insert4}"|"{insert5}"|"{insert6}"|"{prg}"|"{scanm}"|"{spclmsg1}"|"{spclmsg2}"|"{addcol1}"|"{addcol2}"|"{addcol3}"|"{addcol4}"|"{addcol5}"|"{addcol6}"|"{addcol7}"|"{addcol8}"|"{addcol9}"|"{addcol10}"|"{addcol11}"|"{addcol12}"|"{addcol13}"|"{addcol14}"|"{addcol15}"|"{addcol16}"|"{addcol17}"|"{addcol18}"|"{addcol19}"|"{addcol20}"\n'
	fields_to_update = ('cardcode','label','carrier','envelope','insert1','insert2','insert3','insert4','insert5','insert6','addcol1','addcol2','addcol3','addcol4','addcol5')

	def add_document(self, report_config):
		x3_fields = copy.deepcopy(report_config.fields)

		for field in X3.fields_to_update:
			x3_fields[field] = re.sub('[®&?/()# ]', '', x3_fields[field].split('*')[0])[:20]

		x3_fields['filename'] = splitext(x3_fields['filename'])[0]
		x3_fields['label'] = x3_fields['label'].replace('N/A','')
		x3_fields['carrier'] = x3_fields['carrier'].replace('CARD ONLY','').replace('CARDS ONLY','').replace('PLAIN WHITE PAPER','')

		if x3_fields['car'] in ('0', 0): x3_fields['car'] = ''

		self.data.append(X3.x3_layout.format(**x3_fields))

	def finish(self):
		if self.data: TextFile.finish(self)

class Dailies(TextFile):
	df_header = 'Customer|jobname|bin|ext|gcsfile|cqty|fqty|rec|shipdate|custfile|bulk|M1|M2|M3\n'
	df_layout = '{cust}|{jobname}|{bin:.6}|{ext}|{filename}|{qty}|{car}|{rec}|{shipdate}|{custfile}|{bulk}|{m1}|{m2}|{m3}\n'

	def __init__(self, out_filename):
		TextFile.__init__(self, out_filename)
		self.data.append(Dailies.df_header)

	def add_document(self, report_config): self.data.append(Dailies.df_layout.format(**report_config.fields))

	def finish(self):
		if len(self.data) > 1: TextFile.finish(self)

class Inventory(ExcelFile):
	inv_fields = ['gcsno','cust','jobname','bin','filename','qty','cardcode','label','car','carrier','envelope','insert1','insert2','insert3','insert4','insert5','insert6','bulk','m1','m2','m3','barcode']

	def __init__(self, out_filename, sheetname='Sheet 1'):
		ExcelFile.__init__(self, out_filename, sheetname)
		self.data.append(['gc_no','cust','jobname','bin','filename','qty','cardcode','label','car','carrier','envelope','insert1','insert2','insert3','insert4','insert5','insert6','bulk','m1','m2','m3','barcode'])

	def add_document(self, report_config): self.data.append([report_config.fields[field] for field in Inventory.inv_fields])

	def finish(self):
		if len(self.data) > 1: ExcelFile.finish(self)

class Rpt(TextFile):
	def __init__(self, out_filename, job_title=''):
		TextFile.__init__(self, out_filename)
		self.cards = 0
		self.carriers = 0
		self.unprocessed = 0
		self.bad_files = []
		self.data.append(strftime('Valid USA Summary Report for %A - %B %d, %Y').center(96)+'\n'+('<<{}>>'.format(job_title).center(96)+'\n\n' if job_title else '\n'))

	def add_document(self, report_config): pass

class ErrorReport(TextFile):
	def add_document(self, report_config): pass

	def finish(self):
		if self.data: TextFile.finish(self)


# Documents
class Machine(TextFile):
	def __init__(self, out_filename, header=''):
		if len(os.path.basename(out_filename)) > 20: print 'Warning: Filename over 20 characters - ' + os.path.basename(out_filename)
		TextFile.__init__(self, out_filename)
		if header: self.data.append(header)

class Warehouse(TextFile):
	def __init__(self, out_filename):
		TextFile.__init__(self, out_filename)
		self.whs_header = ''
		self.page_header = ''
		self.final_data = []
		self.special_data = []

	def format_data(self, records_per_col=0): # if records_per_col > 0, don't add \n to layout; if records_per_col = 0, add \n to layout
		if records_per_col:
			self.final_data.append(self.whs_header)
			self.data = [self.data[i:i+records_per_col] for i in xrange(0, len(self.data), records_per_col)]
			num_pages = (len(self.data) / 2) + (len(self.data) % 2 > 0)
	
			for page in range(num_pages):
				self.final_data.append(('\n' if page>=1 else '')+self.page_header)
	
				for whs_line in range(len(self.data[page*2])):
					try:
						self.final_data.append(self.data[page*2][whs_line] + self.data[(page*2)+1][whs_line] + '\n')
					except IndexError:
						self.final_data.append(self.data[page*2][whs_line] + '\n')
		else:
			self.final_data = [self.whs_header, self.page_header] + self.data
		self.data = self.final_data + self.special_data

class ReportConfig:
	q = json.load(open(Dirs.references+'fields.json','r'))
	#q = json.load(open(Dirs.references+'fields.json'), object_pairs_hook=OrderedDict)   #if you want them ordered

	def __init__(self, out_filename, job_json_file):
		self.out_filename = out_filename
		self.fields    = copy.deepcopy(ReportConfig.q['fields'])
		self.rs_fields = copy.deepcopy(ReportConfig.q['Release Sheet Fields'])
		self.sd_fields = copy.deepcopy(ReportConfig.q['Ship Detail Fields'])
		self.include_rs, self.include_sd = True, True

		self.fields.update(job_json_file['fields'])

	def transfer_fields(self):
		# fields.json - the name of the json file that contains all fields for rsnsd and reports (dailies/x3/backup/inventory)
		# ReportConfig.q['fields'] - a copy of the fields dictionary inside fields.json
		# self.fields - holds a copy of the fields dictionary inside the respective job's json file

		# adding/updating fields before transferring fields to rs/sd
		self.fields['intradate'] = strftime('%A - %B %d, %Y %I:%M %p')
		self.fields['filename'] = self.fields['filename'].upper()

		# transfer/update fields to rs/sd
		for f in self.fields:
			if f in self.rs_fields.keys():
				self.rs_fields[f]['data'] = self.fields[f].replace('&','&amp;')
			if f in self.sd_fields.keys():
				self.sd_fields[f]['data'] = self.fields[f].replace('&','&amp;')
			if '&amp;' in self.fields[f]:
				self.fields[f] = self.fields[f].replace('&amp;','&')
		
		if not os.path.isfile(Dirs.card_scans+self.fields['scanm']):
			print 'Warning: {} not found. Using noimage.bmp'.format(self.fields['scanm'])
			self.fields['scanm'] = 'noimage.bmp'

		self.rs_fields['scanm']['data'] = Dirs.card_scans + self.fields['scanm']
		self.rs_fields['barcodeString']['data'] = self.fields['filename']
		
		self.sd_fields['barcodeString']['data'] = self.fields['filename']
		
		# adding/updating fields after transferring fields to rs/sd
		self.fields['rec'] = strftime('%m/%d/%y')
		self.fields['ext'] = self.fields['bin'][6:10]
		self.fields['qty'] = '0' if not self.fields['qty'] else self.fields['qty']
		self.fields['car'] = '0' if not self.fields['car'] else self.fields['car']
		if not self.fields['shipdate']: self.fields['shipdate'] = '??'

		for f in self.fields:
			if self.fields[f] == 'Incomplete': print 'Warning: {} still marked as Incomplete.'.format(f)

	def finish(self):
		pages = []
		if self.include_rs:
			PDF_Reports.makeReleaseSheet(self.out_filename+'_RS.pdf', self.rs_fields)
			pages.append(self.out_filename+'_RS.pdf')
		if self.include_sd:
			PDF_Reports.makeShipDetail(self.out_filename+'_SD.pdf', self.sd_fields)
			pages.append(self.out_filename+'_SD.pdf')
		if pages: PDF_Reports.combinePages(self.out_filename, pages=pages)


# Job class
class Job:
	def __init__(self, file_code, client_code, client_name, json_file, src_files=[], letter='', testing=False, job_title='', new_timestamp='', passphrase='default', has_files=True):
		try:
			if not check_directories_and_files(): raise Exception('Could not connect to certain directories and/or files not found!\n')

			# initialize testing, timestamp, base_filename, json_file
			self.testing = testing
			self.timestamp = (new_timestamp if new_timestamp else strftime('%m%d%y')) + letter
			self.base_filename = file_code + self.timestamp
			self.json_file = json.load(open(json_file, 'r'))
			
			# initialize documents/reports
			self.documents = []
			self.reports = {
				'backup':    Backup(Dirs.backup+strftime('Backup_{}_%m%d%Y_%I%M%S.txt').format(client_code)),
				'x3':        X3(Dirs.reports+strftime('x3{}%m%d%y_%I%M%S.csv').format(client_code)),
				'dailies':   Dailies(Dirs.reports+strftime('Dailies_{}_%m%d%y_%I%M%S.txt').format(client_code)),
				'inventory': Inventory(Dirs.inventory+'{}_{}.xlsx'.format(client_name, self.timestamp)),
				'error':     ErrorReport(Dirs.reports+'{}_{}.error'.format(client_name, self.timestamp)),
				'rpt':       Rpt(Dirs.reports+'{}_{}.rpt'.format(client_name, self.timestamp), job_title)
			}
		
			# set up src file operations
			# if testing, will only look for manually placed files in Dirs.raw_files and ignore remaining operations
			self.src_files = src_files
			self.has_files = has_files
			if self.testing:
				# move files in below working directories to Dirs.hold
				for f in (glob(Dirs.backup+'*')+glob(Dirs.reports+'Dailies*')+glob(Dirs.reports+'x3*')+glob(Dirs.return_files+'*.csv')): move_file(f, Dirs.hold)
			else:
				# move files in below working directories to Dirs.hold
				files =	(glob(Dirs.raw_files+'*')+
						 glob(Dirs.stage+'*')+
						 glob(Dirs.reports+'*.*')+
						 glob(Dirs.backup+'*')+
						 glob(Dirs.dumps+'*')+
						 glob(Dirs.inventory+'*')+
						 glob(Dirs.labels+'*')+
						 glob(Dirs.pdf+'*.pdf')+
						 glob(Dirs.return_files+'*')+
						 glob(Dirs.warehouse+'*'))
				if files:
					print '\nWarning: Files detected in Stage/Reports/Raw_Files.\nMoved {} to Hold folder.'.format('\n'.join(files))
					move_to_hold()

				if self.has_files:
					# check if any files at all
					if not self.src_files: raise Exception('Warning: No files detected in input file folder (check at the beginning of the module).')

					# check if files already in Dirs.default
					duplicate_files = [f for f in self.src_files if os.path.isfile(Dirs.default+os.path.basename(f))]
					if duplicate_files: raise Exception('Error: {} already in {}\nExiting the program.'.format('\n'.join(duplicate_files), Dirs.default))
	
					# get HSA passphrase if applicable
					qq = json.load(open(Dirs.references+'HSA_Config.json','r'))
					passphrase = qq[passphrase] if passphrase in qq.keys() else qq['default']
	
					# (decrypt or copy) src_files to Dirs.raw_files, src_files will be moved in finish()
					for src_file in self.src_files:
						if src_file.endswith('.pgp') or src_file.endswith('.gpg') or src_file.endswith('.asc'):
							decrypt_PGP(src_file, Dirs.raw_files, passphrase)
						elif src_file.endswith('.zip'):
							subprocess.call('"C:\\Program Files\\7-Zip\\7z.exe" x "{}" -o"{}"'.format(src_file, Dirs.raw_files))
						else:
							shutil.copy2(src_file, Dirs.raw_files)
						#shutil.move(src_file, Dirs.default)
			self.raw_files = glob(Dirs.raw_files+'*')
		except:
			raise Exception('\n\nError while retrieving files.\n\n' + traceback.format_exc())

	def add_to_documents(self, *files_to_add): self.documents.extend(files_to_add)
			
	def add_to_reports(self, report_config):
		for report in self.reports:
			self.reports[report].add_document(report_config)

	def output_files(self):
		if self.documents:
			# write all reports and documents
			for report in self.reports: self.reports[report].finish()
			for document in self.documents: document.finish()

			if not self.testing:
				for each_report_config in [f for f in self.documents if isinstance(f, ReportConfig)]: HSA_Database.add_to_database(each_report_config) # pass
		else:
			print 'Warning: No Raw Files were processed.\n'
			self.reports['error'].finish()

	def finish(self, print_whs=False, print_pdf=True, delete_pdf=True):
		if not self.testing:
			try:
				print_pages(print_whs, print_pdf, delete_pdf)
			
				if glob(Dirs.stage+'*'): encrypt_to_HSA()
		
				for raw_file in glob(Dirs.raw_files+'*'): os.remove(raw_file)
		
				for backup in glob(Dirs.backup+'*.*'):
					move_file(backup, Dirs.reports_sftp+'\\Daily\\')
		
				for report in glob(Dirs.reports+'*.*'):
					copy_file(report, Dirs.default)
					move_file(report, Dirs.reports_sftp+'\\')
		
				for whs in glob(Dirs.warehouse+'*.whs'):
					copy_file(whs, Dirs.reports_sftp+'\\dumps2share\\', new_filename=splitext(os.path.basename(whs))[0]+'.txt')
					copy_file(whs, Dirs.secure+'DUMPS_QC\\', new_filename=splitext(os.path.basename(whs))[0]+'.txt')
					move_file(whs, 'O:\\dumps\\')
		
				for dmp in glob(Dirs.dumps+'*.dmp'):
					move_file(dump, 'R:\\')
		
				for inv in (glob(Dirs.inventory+'*.xlsx') + glob(Dirs.inventory+'*.xls')):
					move_file(inv, 'O:\\Daily Reports\\')
		
				for label in (glob(Dirs.labels+'*.xlsx') + glob(Dirs.labels+'*.xls')):
					copy_file(label, Dirs.default)
					move_file(label, Dirs.reports_sftp+'\\')

				if self.has_files:
					for src_file in self.src_files:
						move_file(src_file, Dirs.default)
			except:
				raise Exception('\n\nError found while printing/encryping/posting files\n\n' + traceback.format_exc())

if __name__ in '__main__':
	print 'Running a wrong module!!!!'
	pass
