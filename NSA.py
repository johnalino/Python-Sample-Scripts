# coding=utf-8
from os.path import basename
from time import strftime
from FDApproval import MakeApproval
from NSA_Operations import *

class Datadump:
	def __init__(self, jobname=None):
		self.header = [strftime('\t\tValid USA Report %B %d, %Y %H:%M{}\n\n'.format((' - ' + jobname) if jobname else ''))]
		self.body = []
		self.total = 0

	def add_line(self, line):
		self.header.append(line)
	
	def add_file(self, raw_file, processed_file, batch=500, tm=0):
		filename = basename(processed_file)
		self.file_header = None

		with open(processed_file, 'r') as file_read:
			data = file_read.readlines()
			if data[0][0:6] != '000001' and data[0][0:7] != '0000001': self.file_header = data.pop(0)
			self.total += len(data)
	
			self.header.append('{0:<50}has{1:>12,} rcds. {2}batch={3}, tm={4}\n'.format(filename, len(data), raw_file+'; ' if raw_file else '', batch, tm))

			if raw_file:         self.body.append('Cust File: %s\n' % raw_file)	
			self.body.append('VAL File: {} for {:,} rcds\n{}\n'.format(filename, len(data), ('·'*(len(data[0])-1))))
			if self.file_header: self.body.append(self.file_header)
	
			if len(data) > 20:
				for x in range(10):
					self.body.append(data[x])
				self.body.append('\t\t{:,} Records Not Shown.\n'.format(len(data) - 20))
				for x in range(-10,0):
					self.body.append(data[x])
			else:
				for x in range(len(data)):
					self.body.append(data[x])
			self.body.append('\n')

	def finish(self, dump_file_name):
		self.header.append('------------\n'.rjust(66))
		self.header.append('{0:>50}{1:>15,}\n\n'.format('Total records:', self.total))
		with open(dump_file_name, 'w') as fout:
			fout.writelines(self.header)
			fout.writelines(self.body)

class NJob:
	def __init__(self, raw_file, testing=False):
		self.good_to_go = True
		self.testing = testing
		self.raw_file = raw_file
		self.test_data = []
		self.prod_data = []

class FirstData(NJob):
	def __init__(self, raw_file, testing=False):
		NJob.__init__(self, raw_file, testing)
		self.batch = basename(self.raw_file).split('_')[0]
		self.base_filename = ('' if self.testing else Dirs.gift) + self.batch + strftime('_%m%d_')

		with open(self.raw_file,'r') as file_read: self.raw_data = file_read.readlines()[:-1] # To ignore footer
		self.file_header = self.raw_data.pop(0)

	def process_data(self, **static_fields):
		for raw_line in self.raw_data:
			line_info = { 'acct': raw_line[1:17], 'index': 17 } # always ignore first char in line and acct is always 16 digits
		
			FirstData.get_field(self, 'track1', line_info, raw_line) # must be in this order: track1, track2, pin, barc
			FirstData.get_field(self, 'track2', line_info, raw_line)
			FirstData.get_field(self, 'pin',    line_info, raw_line)
			FirstData.get_field(self, 'barc',   line_info, raw_line)

			if '$' in line_info['track1']:
				line_info['upc'] = full_upc(line_info['track1'].split('^')[1].split('$')[0][:11]) # Blackhawk_FD -get from file, check with OCS
				line_info['denom'] = line_info['track1'].split('$')[1]

				if static_fields.get('upc','') and static_fields.get('upc','') != line_info['upc']:
					raise Exception('Unequal upcs! mf={}; other={}'.format(line_info['upc'], static_fields.get('upc',''))) # Incomm_FD -get from file, check with csv
				if static_fields.get('denom','') and static_fields.get('denom','') != line_info['denom']:
					raise Exception('Unequal denoms! mf={}; other={}'.format(line_info['denom'], static_fields.get('denom','')))
		
			line_info['acct4444'] = insert_char(line_info['acct'], 4,4,4,4)
			line_info.update(static_fields)

			self.prod_data.append(line_info)

	def get_field(self, field_name, line_info, raw_line):
		try:
			field_length = int( raw_line[line_info['index'] : line_info['index']+3] )
		except ValueError:
			line_info[field_name] = ''
		else:
			line_info['index'] += 3
			line_info[field_name] = raw_line[line_info['index'] : line_info['index']+field_length]
			line_info['index'] += len(line_info[field_name])

	def make_approval(self, take_from_top=True):
		print 'MakeApproval - ' + self.raw_file
		if take_from_top:
			MakeApproval(self.raw_file, self.raw_data[:3], self.file_header, directory='' if self.testing else Dirs.default)
		else:
			MakeApproval(self.raw_file, self.raw_data[-len(self.test_data):(-len(self.test_data)+3 or None)], self.file_header, directory='' if self.testing else Dirs.default)

class SVS(NJob):
	def __init__(self, raw_file, testing=False):
		NJob.__init__(self, raw_file, testing)
		with open(self.raw_file,'r') as file_read: self.raw_data = file_read.readlines()

		batches = [line for line in self.raw_data if line[0].upper()=='C']
		if len(batches) != 1:
			print '{} should have one batch. Contains {} batches.\nPlease run SVSBatchSplit.py before running SVS related jobs.'.format(self.raw_file, len(batches))
			self.good_to_go = False

		self.batch = self.raw_data[1][1:8]
		self.client_code = self.raw_data[1][8:13]
		self.base_filename = ('' if self.testing else Dirs.gift) + self.batch + strftime('_%m%d_')
		self.test_data = []
		self.prod_data = []

		self.file_headers = self.raw_data[:3]
		self.file_footers = self.raw_data[-2:]
		del self.raw_data[:3], self.raw_data[-2:]

	def process_data(self, **static_fields):
		for raw_line in self.raw_data:
			line_info = {}

			line_info['acct']          = raw_line[1:20].lstrip('0')
			line_info['exp']           = raw_line[20:24]
			line_info['security_code'] = raw_line[24:27]
			line_info['denom']         = raw_line[27:32]
			line_info['track1_cvv']    = raw_line[32:35]
			line_info['track2_cvv']    = raw_line[35:43]
			line_info['pin']           = raw_line[43:47]
			line_info['ssc']           = raw_line[69:73]
			line_info['url']           = raw_line[73:121]
			line_info['barc_ssc']      = '{acct}{ssc}'.format(**line_info)
	
			if len(line_info['acct']) == 19:
				line_info['acct44443'] = insert_char(line_info['acct'], 4,4,4,4,3)
				line_info['acct6481']  = insert_char(line_info['acct'], 6,4,8,1)
				line_info['acct18_1']  = insert_char(line_info['acct'], 18,1)
				line_info['acct6445']  = insert_char(line_info['acct'], 6,4,4,5)
				line_info['acct34444'] = insert_char(line_info['acct'], 3,4,4,4,4)
			line_info.update(static_fields)

			line_info['SVSStandardTrack1'] = 'B{acct}^{client_code:<26}^{exp}{security_code}{track1_cvv}'.format(client_code=self.client_code, **line_info)
			line_info['SVSStandardTrack2'] = '{acct}={exp}{security_code}{track2_cvv}'.format(**line_info)
			if 'upc' in line_info.keys():
				line_info['BHN_Hybrid_Track1'] = 'B{acct}^{upc:.11}${denom}$        ^{exp}{security_code}{track1_cvv}'.format(**line_info) # Blackhawk_SVS -hardcode upc/denom
				line_info['BHN_Hybrid_Track2'] = '{acct}={exp}{security_code}{track2_cvv}'.format(**line_info) # Incomm_SVS -get upc/denom from csv, just check denom

			self.prod_data.append(line_info)

class GiveX(NJob):
	def __init__(self, raw_file, testing=False):
		NJob.__init__(self, raw_file, testing)
		self.base_filename = ('' if testing else Dirs.gift) + self.raw_file.split('_')[0] + strftime('_%m%d_')
		with open(self.raw_file,'r') as file_read: self.raw_data = file_read.readlines()

		for raw_line in self.raw_data:
			self.prod_data.append(
				{'track1': raw_line.split(',')[0].replace('"','').strip(),
				 'track2': raw_line.split(',')[2].replace('"','').strip(),
				 'acct':   raw_line.split(',')[3].replace('"','').strip(),
				 'pin':    raw_line.split(',')[6].replace('"','').strip(),

				 'acct667': insert_char(raw_line.split(',')[3].replace('"','').strip(), 6,6,7)} )

class Speedway(NJob):
	def __init__(self, raw_file, testing=False):
		NJob.__init__(self, raw_file, testing)
		self.base_filename = ('' if testing else Dirs.gift) + 'SPD_' + raw_file.split('.')[0].split('_')[-1] + strftime('_%m%d%y')
		with open(self.raw_file,'r') as file_read: self.raw_data = file_read.readlines()

		for raw_line in self.raw_data:
			self.prod_data.append({
				'acct': raw_line.split()[0].strip(),
				'pin': raw_line.split()[1].strip()
			})

if __name__ in '__main__':
	pass
