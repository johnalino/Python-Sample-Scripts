# coding=utf-8
from xlrd import open_workbook
from HSA import *
from VSP import *
from Label import *

job_info = {
	'src_files': glob(Dirs.src_files+'VSP_SVS Target\\*'),
	'job_title': 'VSP SVS Target',
	'letter': '',
	'new_timestamp': '', #Visa Self Use '032621', UAT New DCPI '021121T', Visa Self Use '012721S', Visa Occasions '012721O', Visa Entertainment-'012721E',  Visa Core- '012721C',Mastercard Core- '012721M',UAT-test-'011921T',UAT-test-'011921T', Holiday Visa additional-'070120V', Holiday Visa-'062920V', Holiday MC-'061820M'
	'testing': False # True#  #############################put back to -1
}

# chris said NO order_id on test card or return file becasue VMS file format do not have it. -June 2020
folder_name = '2021 March-Visa Self Use Rebrand VMS' # the sub-folder that will be created in O:\VSP\SVS Target Live\ only applies if job_info['testing'] = False

split_files = True # If True, it will split in 30,800

make_white_test_files   = True
make_live_samples_files = True# False #
make_prod_files         = True# False #

# 1. adjust above settings and put all card/wrap/snapshot files in Dirs.src_files\SVS Target\
# 2. after running with test=False, manually print/copy files in the above folder_name
# 3. import cn return files and udpate the Bundle Import Log & Timestamps.xlsx

# if you need to optimize even further with memory: move data with zrecords stacked code down to production files section
#		data - proof/label/ctrl/cn, data = data_zrecords(data) - sn.gt1.ald/zs/whs, data = data_stacked_zrecords(data) - gt1/report_config/rpt

def main():
	job = Job('VMST', 'VSP', 'VSP SVS Target', Dirs.references+'VSP.json', **job_info)
	job.raw_files = glob(Dirs.raw_files+'*.csv')
	cmd_files = TextFile(Dirs.return_files+job.base_filename+'_cmd files.txt')
	cn_reference = CN_Reference(Dirs.return_files+job.base_filename+'_cn reference.csv')

	# extract snapshot info
	snapshot_info = {}
	dpci_lookup_info = {}
	for snapshot in glob(Dirs.raw_files+'*.xlsx'):
		wb = open_workbook(snapshot)
		
		# Versions sheet
		try: sh = wb.sheet_by_name('Versions')
		except:
			print wb + ' is missing sheet: Versions. Skipping this snapshot. This snapshot\'s info won\'t be included in snapshot_info/dpci_lookup_info.'
			continue

		keys = {}
		for col in range(sh.ncols):
			k = sh.cell(1, col).value.strip()
			if k: keys[k] = col
	
		# Versions - check headers
		if any([k not in job.json_file['snapshot_headers_target'] for k in keys]):
			print 'Warning - ' + basename(snapshot) + ' has unknown keys: ' + ', '.join([k for k in keys if k not in job.json_file['snapshot_headers_target']])
		if any([rk not in keys.keys() for rk in job.json_file['snapshot_headers_target']]):
			raise Exception(basename(snapshot) + ' is missing keys: ' + ', '.join([rk for rk in job.json_file['snapshot_headers_target'] if rk not in keys.keys()]))

		for row in range(2, sh.nrows):
			# check order_id duplicates
			try:
				##order ID is not in cardshell file name for VMS file layout so use full file name, prod ID will not needed for return file or print on test card per chris 6.15.20
				#order_id = str(int(sh.cell(row, keys['Order ID']).value)).strip()
				order_id = str(sh.cell(row, keys['Order ID']).value).strip().upper()
			except:
				print 'Warning - {} has invalid order_id value on row {} (Skipping this row): {}'.format(basename(snapshot), row, sh.cell(row, keys['Order ID']).value)
				continue
			if order_id in snapshot_info.keys(): raise Exception(order_id + ' is already in snapshot_info! Check all rows/snapshots for duplicates.')
		
			snapshot_info[order_id] = {}
			for k in job.json_file['snapshot_headers_target']:
				v = sh.cell(row, keys[k]).value
				try:
					snapshot_info[order_id][k] = unicode(int(v)).strip()
				except:
					snapshot_info[order_id][k] = unicode(v).strip()

		# DPCI-Lookup sheet
		try: sh = wb.sheet_by_name('DPCI-Lookup')
		except:
			print wb + ' is missing sheet: DPCI-Lookup. Skipping this snapshot. This snapshot\'s info won\'t be included in dpci_lookup_info.'
			continue

		keys = {}
		for col in range(2, sh.ncols):
			k = sh.cell(0, col).value.strip()
			if k: keys[k] = col

		# DPCI-lookup - check headers
		if any([k not in job.json_file['lookup_headers_target'] for k in keys]):
			print 'Warning - ' + basename(snapshot) + ' has unknown keys: ' + ', '.join([k for k in keys if k not in job.json_file['lookup_headers_target']])
		if any([rk not in keys.keys() for rk in job.json_file['lookup_headers_target']]):
			raise Exception(basename(snapshot) + ' is missing keys: ' + ', '.join([rk for rk in job.json_file['lookup_headers_target'] if rk not in keys.keys()]))

		for row in range(1, sh.nrows):
			try:
				
				prod_id = str(int(sh.cell(row, keys['Prod ID']).value)).strip().zfill(4)
				
			except:
				print 'Warning - {} has invalid prod_id value on row {} (Skipping this row): {}'.format(basename(snapshot), row, sh.cell(row, keys['Prod ID']).value)
				continue
			if not prod_id or prod_id in dpci_lookup_info.keys(): continue

			dpci_lookup_info[prod_id] = {}
			for k in job.json_file['lookup_headers_target']:
				v = sh.cell(row, keys[k]).value
				try:
					dpci_lookup_info[prod_id][k] = unicode(int(v)).strip()
				except:
					dpci_lookup_info[prod_id][k] = unicode(v).strip()

	for rf, card_file in enumerate(job.raw_files):
		print '\n\n' + card_file
		data, data_zrecords, data_stacked_zrecords = None, None, None

		#for key, value in snapshot_info.iteritems() :
			#print key, value
		print snapshot_info.keys()
		#order_id = basename(card_file).split('_')[1]
		## use full file name, no order id in file name for VMS file format
		
		order_id = basename(card_file).upper()
		#order_id = '_'.join(basename(card_file).split('_')[:5]) #basename(card_file).split('_')[:4]
		if order_id not in snapshot_info.keys(): raise Exception('\n\nCould not find {} in any snapshot!\n\n'.format(order_id))
		version_info = snapshot_info[order_id]

		with open(card_file, 'r') as fr: card_data = fr.readlines()[1:-1] #############################put back to -1
		wrap_file = glob(Dirs.raw_files+'*'+version_info['File ID']+'*')
		if len(wrap_file) != 1: raise Exception('Found {} instances of the wrap file: {}'.format(len(wrap_file), version_info['File ID']))
		with open(wrap_file[0],'r') as fr: wrap_data = fr.readlines()[1:]
		#############################put back to next 3 lines
		if len(card_data) != len(wrap_data): raise Exception('Card/Wrap data have different lengths: c={}, w={}'.format(len(card_data), len(wrap_data)))
		if len(card_data) != int(version_info['Quantity'].replace(',','')):
			raise Exception('Card/Snapshot quantities are different: c={}, s={}'.format(len(card_data), int(version_info['Quantity'].replace(',',''))))

		pack_id= card_data[0][8:12] #not sure if need it. use for cn file in vsto format
		src_platform = basename(card_file).split('_')[1] #not sure if need it. use for cn file in vsto format
		sequencenbr = basename(card_file).split('_')[5]  #not sure if need it. use for cn file in vsto format
		ffid = basename(wrap_file[0]).split('_')[4]
		white_tests = int(version_info['White Tests']) #job.json_file['files'][basename(card_file)]['white_tests']
		live_samples = int(version_info['Live Samples']) #job.json_file['files'][basename(card_file)]['live_samples']
		bundle = int(version_info['Bundle']) #job.json_file['files'][basename(card_file)]['bundle']
		master = int(version_info['Master']) #job.json_file['files'][basename(card_file)]['master']
		pallet = int(version_info['Pallet']) #job.json_file['files'][basename(card_file)]['pallet']

		# 1 - parse data; no z records, no stack
		data = []
		for line in range(len(card_data)):
			if card_data[line][12:31] != card_data[line][47:66]: print 'mismatch - acct - ' + str(line)
			if card_data[line][31:35] != card_data[line][66:70]: print 'mismatch - exp  - ' + str(line)
			if card_data[line][39:42] != card_data[line][70:73]: print 'mismatch - res  - ' + str(line)
			if card_data[line][42:47] != card_data[line][73:78]: print 'mismatch - pin  - ' + str(line)
			if card_data[line][100:126] != card_data[line][126:152]: print 'mismatch - ln3/t1_name - ' + str(line)

			line_info = {
				'acct': card_data[line][12:31].strip(),
				't1_exp': card_data[line][31:35].strip(),
				'eff_date': card_data[line][35:39].strip(),
				'res_type': card_data[line][39:42].strip(),
				'tcvv': card_data[line][78:83].strip(),
				'lang_code': card_data[line][83:85].strip(),
				'cvv': card_data[line][85:88].strip(),
				'pin': card_data[line][88:92].strip(),
				'fullname': card_data[line][100:126].strip().upper(),
				'ln3':  card_data[line][126:152].strip().upper(),
				'magic_number': card_data[line][314:334].strip(),
				'ctrl_number':      wrap_data[line].split(',')[1],
				
				'm23': '',
				'zrecord': '',
				'zrzp': '',
				'bundle_end': '*' if (((line+1) % bundle == 0) and ((line+1) > live_samples+white_tests)) or ((line+1) == live_samples+white_tests) else '',
				'master_end': '**' if (((line-live_samples-white_tests+1) % master == 0) and (line+1 > live_samples+white_tests)) or ((line+1) == live_samples+white_tests) else '',

			}
			line_info['prod_id'] = version_info['GC Prod ID']
			#no prod_ID in cardshells file name but have it in each version on snap shot
			if line_info['prod_id'] not in dpci_lookup_info.keys(): raise Exception('Could not find Prod ID {} in DPCI lookup!'.format(line_info[prod_id]))
			lookup_info = dpci_lookup_info[line_info['prod_id']]
			
			if version_info['Product UPC'][:11] != lookup_info['Prod UPC'][:11] or version_info['Product UPC'][:11] != wrap_data[line].split(',')[5][:11]:
				raise Exception('upc mismatch: version_info={}, lookup_info={}, wrap_data={}'.format(version_info['Product UPC'], lookup_info['Prod UPC'], wrap_data[line].split(',')[5]))
			# put back 
			if version_info['Packing UPC'] != lookup_info['Packing UPC']:
				raise Exception('packing upc mismatch: version_info={}, lookup_info={}'.format(version_info['Packing UPC'], lookup_info['Packing UPC']))
			if lookup_info['Denom'] != basename(wrap_file[0]).split('_')[2].lstrip('0')[:-2]:
				raise Exception('denom mismatch: lookup_info={}, wrap_file={}'.format(lookup_info['Denom'], basename(wrap_file[0]).split('_')[2].lstrip('0')[:-2]))


			line_info['acct-1'] = line_info['acct'][:4]
			line_info['acct-2'] = line_info['acct'][4:8]
			line_info['acct-3'] = line_info['acct'][8:12]
			line_info['acct-4'] = line_info['acct'][12:]
			line_info['acct_second_half'] = '{acct-3}{acct-4}'.format(**line_info)
			line_info['magic_number_last6'] = line_info['magic_number'][-6:]
			line_info['exp'] = line_info['t1_exp'][-2:] + '/' + line_info['t1_exp'][:2]
			line_info['track1'] = 'B{acct}^{fullname}^{t1_exp}{res_type}1000000{tcvv}000000'.format(**line_info)
			line_info['track2'] = '{acct}={t1_exp}{res_type}10000{tcvv}'.format(**line_info)
			line_info['denom'] = lookup_info['Denom']
			line_info['dpci324'] = lookup_info['DPCI']
			line_info['barc_tgt'] = '{code_dpci_checkdigit}{ctrl_number}'.format(code_dpci_checkdigit=lookup_info['Code/DPCI/Check Digit'], **line_info)
			if (len(line_info['dpci324'].replace(' ','')) != 9 or
				len(line_info['barc_tgt']) != 25 or
				line_info['barc_tgt'][:14] != target_barcode(line_info['dpci324'].replace(' ',''), line_info['denom'].zfill(3))):
				raise Exception('check DPCI and target barcode: dpci={dpci324}, barc_tgt={barc_tgt:.14}, target_barcode={tb}'.format(
					tb=target_barcode(line_info['dpci324'].replace(' ',''), line_info['denom'].zfill(3)), **line_info))

			del line_info['acct'], line_info['t1_exp'], line_info['res_type']


			line_info['van'] = wrap_data[line].split(',')[3].strip()

			data.append(line_info)
		
		for record in data:
			#put back
			if record['ln3'] != version_info['Embossed Line']:
				raise Exception('Card/Snapshot Embossed Line values are different: magic_number={}, c={}, s={}'.format(record['magic_number'], record['ln3'], version_info['Embossed Line']))

		del card_data, wrap_data  # delete raw card/wrap data to save face

		white_test_data = [data.pop(0) for i in range(white_tests)] if white_tests else []
		live_sample_data = [data.pop(0) for i in range(live_samples)] if live_samples else []

		# data with zrecords stacked (in that order)######################################################################
		if make_prod_files and data:
			data_zrecords = add_zrecords(data)
			data_stacked_zrecords = stack_data(data_zrecords)
	
		filename_white_tests = job.base_filename + chr(97+rf) + '01'
		filename_live_samples = job.base_filename + chr(97+rf) + '02'
		filename = job.base_filename + chr(97+rf) + '03'

		job.reports['rpt'].add_line('{}, {}\n'.format(basename(card_file), basename(wrap_file[0]))) ## for rpt file

		#release sheet
		fields = {
			"cust": "SVS",
			"encoding": "Track 1 and 2 - HiCoe",
			"ultrafront": "DOD 3 Lines",
			"ultraback": "DOD ctrl#, denom, barcode HR",
			"color_ub": "Black",
			"indentbck": "3 Digits - CVV",
			"color_ib": "Black",
			"bulk": "see snapshot/csr",
			"prg": "VSP_SVS_Target VMS.py",
			"scanm": "noimage.bmp",
			"csr": "Cindy",
			"CCode": "SVS"
		}
		fields['bin'] = version_info['Bin number']     ##
		fields['color_uf'] = version_info['Front DOD']
		fields['color_ub'] = version_info['Back DOD']
		fields['shipdate'] = sla_date(30)
		fields['custfile'] = basename(card_file)

		# white test files
		if make_white_test_files and white_test_data:
			print 'White tests: {:,}'.format(white_tests)

			make_az(filename_white_tests+'', white_test_data, job.json_file['headers_az_target_test'], job.json_file['layout_az_target_test'], testing=job_info['testing'], po_number=version_info['PO Number'], order_id='',jobname=lookup_info['Product Description'], upc=lookup_info['Prod UPC'])

			# machine, gt1, sn, tc, cn, whs, report setup, rpt
			make_machine(filename_white_tests, white_test_data, job.json_file['layout_thermal_target'], po_number=version_info['PO Number'], order_id='',
				jobname=lookup_info['Product Description'], upc=lookup_info['Prod UPC'])
			make_gt1(filename_white_tests, white_test_data, job.json_file['headers_gt1_target'], job.json_file['layout_gt1_target'])
			make_sn(filename_white_tests, white_test_data, 'magic_number')
			make_tc(filename_white_tests, version_info['Carrier Front'], version_info['T&C Part#'])
			cn_reference.update_fields(filename=filename_white_tests, order_id='', ffid=ffid, description=lookup_info['Product Description'])
			make_cn(filename_white_tests, white_test_data, 'greencardvms', cn_reference, order_id='')
			make_cn(filename_white_tests, white_test_data, 'vspto', cn_reference, src_platform=src_platform, pack_id=pack_id, sequencenbr=sequencenbr)
			
			make_whs(filename_white_tests, white_test_data)
			make_report_setup(filename_white_tests, job, job_info, qty='{:,}'.format(len(white_test_data)), car='0', jobname=lookup_info['Product Description']+' (White Tests)', cardcode='blank-white',
				**fields)
			update_rpt(filename_white_tests, len(white_test_data), job, lookup_info['Product Description'])

		# live sample files
		if make_live_samples_files and live_sample_data:
			print 'Live Samples: {:,}'.format(live_samples)

			# gt1, sn, tc, ctrl, cmd, cn, whs, report setup, rpt
			make_gt1(filename_live_samples, live_sample_data, job.json_file['headers_gt1_target'], job.json_file['layout_gt1_target'])
			make_sn(filename_live_samples, live_sample_data, 'magic_number')
			make_tc(filename_live_samples, version_info['Carrier Front'], version_info['T&C Part#'])
			make_ctrl(filename_live_samples, [record['ctrl_number'] for record in live_sample_data])
			make_cmd(filename_live_samples, 'target', cmd_files, ctrl_filename=Dirs.return_files+filename_live_samples+'_control numbers.txt', bundle=bundle, master=master, pallet=pallet,
				upc=lookup_info['Prod UPC'], header=lookup_info['Product Description'], jobdate=strftime('%m/%y'), validjob=filename_live_samples, dpci=lookup_info['DPCI'].replace(' ',''),
				packingupc=lookup_info['Packing UPC'])
			cn_reference.update_fields(filename=filename_live_samples, order_id='', ffid=ffid, description=lookup_info['Product Description'])
			make_cn(filename_live_samples, live_sample_data, 'greencardvms', cn_reference, order_id='')
			make_cn(filename_live_samples, live_sample_data, 'vspto', cn_reference, src_platform=src_platform, pack_id=pack_id, sequencenbr=sequencenbr)

			make_whs(filename_live_samples, live_sample_data)
			make_report_setup(filename_live_samples, job, job_info, qty='{:,}'.format(len(live_sample_data)), car='{:,}'.format(len(live_sample_data)),
				jobname=lookup_info['Product Description']+' (Live Samples)', cardcode=version_info['Card SV'], carrier=version_info['Carrier Front'], insert1=version_info['T&C Part#'],
				addcol1=version_info['Carrier Back'], **fields)
			update_rpt(filename_live_samples, len(live_sample_data), job, lookup_info['Product Description'])

		# production files
		if make_prod_files and data:
			print 'Production (full): {:,}'.format(len(data))

			# proofs, ctrl, cmd, cn
			make_proofs(filename, data, job.json_file['card_proof_layout_target'], job.json_file['wrap_proof_layout_target'], job.json_file['label_proof_layout_target'], upc=lookup_info['Prod UPC'])
			make_ctrl(filename, [record['ctrl_number'] for record in data]) ## make file with number to create label for client that go into bundler
			make_cmd(filename, 'target', cmd_files, ctrl_filename=Dirs.return_files+filename+'_control numbers.txt', bundle=bundle, master=master, pallet=pallet,
				upc=lookup_info['Prod UPC'], header=lookup_info['Product Description'], jobdate=strftime('%m/%y'), validjob=filename, dpci=lookup_info['DPCI'].replace(' ',''),
				packingupc=lookup_info['Packing UPC'])
			cn_reference.update_fields(filename=filename, order_id='', ffid=ffid, description=lookup_info['Product Description'])
			make_cn(filename, data, 'greencardvms', cn_reference, order_id='')  #make imcomplete return file (still missing start, end bundle, master, pallet from bundler)
			make_cn(filename, data, 'vspto', cn_reference, src_platform=src_platform, pack_id=pack_id, sequencenbr=sequencenbr)

			# WIP label start
			label1000 = Label([], Dirs.labels+filename+'T1000_Standard.xlsx', 1000)
			label500 = Label([], Dirs.labels+filename+'T500_Standard.xlsx', 500)
			label1000.data.append(['Filename','Sequence # Start','Sequence # End','Tray Number','Qty','Jobname']) # data is from label1000 object so it's blank list at the moment until append
			label500.data.append(['Filename','Sequence # Start','Sequence # End','Tray Number','Qty','Jobname'])

			#split into batch of 30800(pallet qty) if set variable split_files equal true 
			data = split_with_zrecords(data) if split_files else [data] #data now is a list of list
			for i, data_split in enumerate(data, 1):
				index = '-{:0>2}'.format(i)

				# make az file
				make_az(filename+index, data_split, job.json_file['headers_az_target'], job.json_file['layout_az_target'], testing=job_info['testing'])

				# label add
				add_to_label(label1000, [r['magic_number'] for r in data_split], filename+index, lookup_info['Product Description'])  # do the calculation and combine mutiple label files into 1 file for LIsa
				add_to_label(label500, [r['magic_number'] for r in data_split], filename+index, lookup_info['Product Description'])
			label1000.finish() # write to excel file 
			label500.finish()

			data_zrecords = split_with_zrecords(data_zrecords) if split_files else [data_zrecords]
			for i, data_zrecords_split in enumerate(data_zrecords, 1):
				index = '-{:0>2}'.format(i)
				# zrecords list, sn, tc, whs
				total_zrecords = make_zrecords_list(filename+index, data_zrecords_split)
				make_sn(filename+index, data_zrecords_split, 'magic_number')
				make_tc(filename+index, version_info['Carrier Front'], version_info['T&C Part#'])
				make_whs(filename+index, data_zrecords_split)

				data_stacked_zrecords_split = stack_data(data_zrecords_split)
				# gt1, report setup, rpt
				make_gt1(filename+index, data_stacked_zrecords_split, job.json_file['headers_gt1_target'], job.json_file['layout_gt1_target'])
				make_report_setup(filename+index, job, job_info, qty='{:,}'.format(len(data_stacked_zrecords_split)), car='{:,}'.format(len(data_stacked_zrecords_split)), ##create release sheet, ship detail and dailies and X3 inventory and back up
					jobname=lookup_info['Product Description'], cardcode=version_info['Card SV'], spclmsg1='{:,} total z records.'.format(total_zrecords), carrier=version_info['Carrier Front'],
					insert1=version_info['T&C Part#'], addcol1=version_info['Carrier Back'], **fields)
				update_rpt(filename+index, len(data_stacked_zrecords_split), job, lookup_info['Product Description'], total_zrecords=total_zrecords)

		job.reports['rpt'].add_line('\n')

	job.add_to_documents(cmd_files, cn_reference)
	job.reports['rpt'].add_line('{:>54}\n{:>53,} Total records\n'.format('--------', job.reports['rpt'].cards))
	job.output_files()
	#job.finish()

	if not job_info['testing']:
		if not os.path.isdir('O:\\VSP\\SVS Target Live\\'+folder_name): os.mkdir('O:\\VSP\\SVS Target Live\\'+folder_name)
		if not os.path.isdir('O:\\VSP\\SVS Target Live\\'+folder_name+'\\cn files'): os.mkdir('O:\\VSP\\SVS Target Live\\'+folder_name+'\\cn files')
		subprocess.call('pgp.exe -e -r "PES2" -r "Valid HSA" {}*.sn.* --input-cleanup wipe --output {}'.format(Dirs.stage, Dirs.secure+'VSP\\SN\\'))
		subprocess.call('pgp.exe -e -r "PES2" -r "Valid HSA" {}*.tc.* --input-cleanup wipe --output {}'.format(Dirs.stage, Dirs.secure+'VSP\\TC\\'))
		subprocess.call('pgp.exe -e -r "PES2" -r "Valid HSA" {}* --input-cleanup wipe --output {}'.format(Dirs.stage, Dirs.secure+'VSP\\'))
		for each in glob(Dirs.warehouse+'*.whs'):
			#move_file(each, 'O:\\VSP\\SVS Target Live\\July\\')
			copy_file(each, Dirs.reports_sftp+'dumps2share\\', new_filename=splitext(os.path.basename(each))[0]+'.txt')
			copy_file(each, Dirs.secure+'DUMPS_QC\\', new_filename=splitext(os.path.basename(each))[0]+'.txt')
			move_file(each, 'O:\\dumps\\')
		for each in glob(Dirs.pdf+'*.pdf') + glob(Dirs.reports+'*.*') + glob(Dirs.backup+'*.*') + glob(Dirs.inventory+'*.xlsx'):
			move_file(each, 'O:\\VSP\\SVS Target Live\\'+folder_name)
		for each in glob(Dirs.return_files+'*'):
			move_file(each, 'O:\\VSP\\SVS Target Live\\'+folder_name+'\\cn files')
		for each in glob(Dirs.raw_files+'*'): os.remove(each)
		finish_labels(strftime('O:\\VSP\\SVS Target Live\\{0}\\SVS Target_{0}_Labels_%m%d%y.zip'.format(folder_name)))

def dpci_checkdigit(dpci):
	total = 0
	for base, d in enumerate([int(n) for n in dpci]):
		product = d * (1 if base % 2 == 0 else 2)
		if product >= 10:
			total += sum(int(i) for i in str(product))
		else:
			total += product
	return total % 10

def target_barcode(dpci, denom):
	digits = [int(d) for d in str(dpci)]
	total = 0
	for d, digit in enumerate(digits[::-1]):
		base = 1 if d%2==0 else 2
		total += sum(int(n) for n in str(digit * base))
	check_digit = total % 10
	return '2' + str(dpci) + str(check_digit) + str(denom)

if __name__ in '__main__':
	try: main()
	except: error()
