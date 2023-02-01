# coding=utf-8
import time, copy, json, subprocess
from HSA import *

vsp = json.load(open(Dirs.references+'VSP.json','r'))

# Z Record CodeZRecordStack
stack_qty = 1000
zstack_qty = 10

class ZRecord:
	def __init__(self):
		self.info = {
			'zrecord': ' ',
			'zrzp': '  ZP',
			'ln3': '',
			'ctrl_number': '',
			'track1': '',
			'track2': '',
			'barc_tgt': '',
			'barc': '',
			'barc-1': '',
			'barc-2': '',
			'barc-3': '',
			'dpci324': '000 00 0000',
		
			'm23': ' ',
			'bundle_end': '',
			'master_end': '',
			'acct-1': '0000',
			'acct-2': '0000',
			'acct-3': '0000',
			'acct-4': '0000',
			'exp': '00/00',
			'cvv': '000',
			'payloadid': '000000',
			'denom': ''
		}

class ZRecordStack:
	def __init__(self, bundle, record):
		self.zrecord_stack = [ZRecord().info for i in range(bundle+1)]
		self.zrecord_stack[0]['zrecord'] = '*'
		self.zrecord_stack[0]['zrzp'] = 'ZR  '

		for z in self.zrecord_stack:
			z['denom'] = '0' * len(record['denom'])
			z['ln3'] = record['ln3']
			z['ctrl_number'] = record['ctrl_number'][-6:].zfill(11)

			if 'pin' in record.keys() and record['track1'][1:2]=='3':
				## USE FOR AMFEX TARGET
				z['track1'] = 'B000000000000000^{fullname:<26}^0000000000000000                '.format(**record)
				z['track2'] = '000000000000000=000000000000000000000'.format(**record)
			else:
				##USE FOR SVS-VISA TARGET
				z['track1'] = 'B0000000000000000^{fullname}^00000000000000000000000'.format(**record)
				z['track2'] = '0000000000000000=000000000000{tcvv}'.format(**record)
			if 'barc_tgt' in record.keys(): z['barc_tgt'] = record['barc_tgt'][-6:].zfill(25)
			if 'barc' in record.keys():
				z['barc'] = record['barc'][-6:].zfill(30)
				z['barc-1'] = z['barc'][:6]
				z['barc-2'] = z['barc'][6:11]
				z['barc-3'] = z['barc'][11:]
			#z['magic_number'] = record['magic_number'][-6:].zfill(9)
			z['magic_number'] = record['magic_number'][-6:].zfill(len(record['magic_number']))
			if 'magic_number_last6' in record.keys(): z['magic_number_last6'] = z['magic_number'][-6:]
			if 'acct_second_half' in record.keys(): z['acct_second_half'] = '00000000'
			if 'pin' in record.keys(): z['pin'] = '0000' ## CID/PIN uses in Amex target
			if 'acct465' in record.keys(): z['acct465'] = '0000 000000 00000' ##  uses in Amex target

def zrecord_frequency(quantity):
	if quantity <= 35000:
		return 1000
	elif quantity <= 150000:
		return 2000
	elif quantity <= 500000:
		return 2500
	elif quantity <= 1000000:
		return 5000
	elif quantity <= 1500000:
		return 7500
	elif quantity <= 2500000:
		return 10000
	else:
		return 15000

def add_zrecords(data):
	zrecord_packout = zrecord_frequency(len(data))
	data_zrecords = []
	index = 0
	data_zrecords.extend(ZRecordStack(zstack_qty, data[index]).zrecord_stack) ## first group of zrecord (total of 11 records)
	
	for each_split in [len(data[i:i+zrecord_packout]) for i in xrange(0, len(data), zrecord_packout)]:  ##balance of zrecord groups
		#print index
		data_zrecords.extend(copy.deepcopy(data[index:index+zrecord_packout]))  ##add data to new list
		index += each_split - (1 if index+each_split == len(data) else 0)   ##increment index by the split
		data_zrecords.extend(ZRecordStack(zstack_qty, data[index]).zrecord_stack) # if index+each_split != len(data):  add another group of zrecord

	return data_zrecords

# data operations - stacking and splitting
def stack_data(data):
	# stack by ctrl_number or magic_number?

	data_stacked = []
	index = 0
	#start_num = int(data[0]['magic_number'][-1]) # int(data[0]['ctrl_number'][-1]) ## uncomment this line when use correct stacking intead of alway stacking at zero!!!
	while index < len(data):
		data_split = []
		split_index = 0
		while index < len(data) and split_index < stack_qty:
			data_split.append(copy.deepcopy(data[index])) ##copy data record data_split list
			if data[index]['zrzp'] not in ('ZR  ','  ZP'): split_index += 1  ## not counting  the zreocds to the split_index 
			index += 1

		numbers = {'0': [], '1': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '8': [], '9': []}
		for record in data_split:
			numbers[record['ctrl_number'][-1]].append(record)  
		#for i in (range(start_num, 10) + range(0, start_num)): data_stacked.extend(numbers[str(i)]) ## stack using the last digit of the start record of the input file.  
		for i in range(10): data_stacked.extend(numbers[str(i)])## stacking always start at zero-- no no

	return data_stacked

def split_with_zrecords(data,batchsplit=30800):
	data_split_with_zrecords = []
	
	while data:
		index = 0
		data_split = []
		while data and index < batchsplit:
			if data[0]['zrzp'] not in ('ZR  ','  ZP'): index += 1
			data_split.append(data.pop(0)) ## this return a item in a list to a new list and delete same item (delete and assign the same time)
		data_split_with_zrecords.append(data_split)

	return data_split_with_zrecords

# bundler functions
def bundle_prep_full(cmd_file):
	with open(cmd_file,'r') as fr: cm_files = fr.readlines() ## file with all the command line files
	for line in cm_files:
		with open(line.strip(),'r') as fr:  ## open and read one command line file as a time
			p = subprocess.Popen(fr.read())  # excuate the command line to import to bundler
			p.wait()
			time.sleep(3)
			print line.strip() + ' - done importing'

def bundle_prep(cm_file):
	with open(cm_file,'r') as fr: subprocess.call(fr.read())

def bundle_get(job_number):
	subprocess.call(Dirs.programs+'SVS_BundlerReturnFile\\bundlerReturnFile  -j {} -p {}'.format(job_number, Dirs.return_files))
	#subprocess.call(Dirs.programs+'SVS_BundlerReturnFile\\bundlerReturnFile -t 2000 -j {} -p {}'.format(job_number, Dirs.return_files))

def bundle_connect(cn_file, br_file):
	if basename(cn_file).split('_')[3].endswith('01') or basename(cn_file).split('_')[3].endswith('01p'): return
	if basename(splitext(cn_file)[0]).split('_')[3] != basename(br_file).split('_')[0]:
		print 'Job names not matching: cn_file = {}, br_file = {}'.format(basename(splitext(cn_file)[0]).split('_')[3], basename(br_file).split('_')[0])
	else:
		multipack = splitext(basename(cn_file))[0].split('_')[3].endswith('p')
		with open(cn_file,'r') as fr: cn_data = fr.readlines()
		with open(br_file,'r') as fr: br_data = fr.readlines()

		if (len(cn_data) != len(br_data) and not multipack) or (len(cn_data)-1 != (len(br_data)-1)*3 and multipack):
			print 'Unequal file lengths (Multipack={}): {} = {}, {} = {}'.format(multipack, basename(cn_file), len(cn_data), basename(br_file), len(br_data))
		else:
			with open(cn_file,'w') as fw:
				fw.write(cn_data.pop(0))
				del br_data[0]
				index = 0
				for line in range(len(cn_data)):
					if cn_data[line].split(',')[-1 if multipack else 11].strip() != br_data[index].split(',')[0]:
						print 'Unequal control numbers (Multipack={}): {} = {}, {} = {}'.format(
							multipack, basename(cn_file), cn_data[line].split(',')[-1 if multipack else 11].strip(), basename(br_file), br_data[index].split(',')[0])
					master_data = '0000000' if '_LiveSamples' in basename(cn_file) else br_data[index].split(',')[2].zfill(7)
					pallet_data = '000000' if '_LiveSamples' in basename(cn_file) else br_data[index].split(',')[3].zfill(6)
					fw.write(','.join(cn_data[line].split(',')[:8])+
						',B'+br_data[index].split(',')[1].zfill(8)+',C'+master_data+',P'+pallet_data+','+
						','.join(cn_data[line].split(',')[11:]))
					index += 1 if not multipack or multipack and (line+1)%3==0 else 0

def bundle_connect_cn_reference():
	cn_reference_file = glob(Dirs.return_files+'*_cn reference.csv')
	if len(cn_reference_file) != 1:
		print 'Found {} instances of cn_reference file\n'.format(len(cn_reference_file))
		return
	else:
		with open(cn_reference_file[0],'r') as fr: cnr_data = fr.readlines()
		cnr_header = cnr_data.pop(0)

		for each in glob(Dirs.return_files+'*_ReturnFile.csv'):
			with open(each,'r') as fr: br_data = fr.readlines()[1:]

			for line in range(len(cnr_data)):
				if cnr_data[line].split(',')[0] == br_data[0].split(',')[-1].strip():
					bundle_start = br_data[0].split(',')[1]
					master_start = br_data[0].split(',')[2]
					pallet_start = br_data[0].split(',')[3]
					bundle_end = br_data[-1].split(',')[1] if br_data[-1].split(',')[1] != bundle_start else ''
					master_end = br_data[-1].split(',')[2] if br_data[-1].split(',')[2] != master_start else ''
					pallet_end = br_data[-1].split(',')[3] if br_data[-1].split(',')[3] != pallet_start else ''
					cnr_data[line] = '{},{},{},{},{},{},{},{}'.format(
						cnr_data[line].split(',')[0],bundle_start,bundle_end,master_start,master_end,pallet_start,pallet_end,','.join(cnr_data[line].split(',')[7:]))
					continue

		with open(cn_reference_file[0],'w') as fw:
			fw.write(cnr_header)
			fw.writelines(cnr_data)

def encrypt_incomm_return():
	subprocess.call('pgp.exe -e -r "incomm" -r "Valid USA" {}CCTO*.csv --input-cleanup wipe --output "{}'.format(Dirs.return_files, 'O:\\VSP\\Return Files\\'))
	subprocess.call('pgp.exe -e -r "incomm" -r "Valid USA" {}VSPTO_VMS_*.csv --input-cleanup wipe --output "{}'.format(Dirs.return_files, 'O:\\VSP\\Return Files\\'))

def import_to_bundler(encrypt=True):
	
	# read in cmd files.txt and run each command line file to import to bundler
	cmd_file = glob(Dirs.return_files+'*cmd files.txt')[0]
	bundle_prep_full(cmd_file)
	time.sleep(3)
	
	# retrieve data from bundler to create return files
	with open(cmd_file,'r') as fr: data = fr.readlines()
	for line in data: bundle_get(basename(line).split('_')[0])
	time.sleep(3)
	
	# merge the incomplete return file with the file from the bundler to create the final return file
	for i in glob(Dirs.return_files+'CCTO*.csv'):
		job_number = basename(splitext(i)[0]).split('_')[3]
		bundle_connect(i, Dirs.return_files+job_number+'_ReturnFile.csv')
	bundle_connect_cn_reference()
	time.sleep(3)

	# encrypt to O:\VSP\Return Files\
	if encrypt: encrypt_incomm_return()

# file operations - split gt1 file
def split_gt1(filename, *splits):
	with open(Dirs.stage+filename,'r') as fr: full_data = fr.readlines()
	header = full_data.pop(0)
	qty_real_records = len([record for record in full_data if record.split('~')[2] not in ('ZR  ','  ZP')])
	if sum(splits) != qty_real_records: raise Exception('Unequal qtys: splits={:,}; file={:,} real records'.format(sum(splits), qty_real_records))

	data = []
	for each_split in splits:
		index = 0
		split_data = []
		while index < each_split:
			if full_data[0].split('~')[2] not in ('ZR  ','  ZP'): index += 1
			split_data.append(full_data.pop(0))
		data.append(split_data)
	if full_data: data[-1].extend(full_data)

	for i, each in enumerate(data, 1):
		with open(Dirs.stage+filename.split('.')[0]+'-{:0>2}.'.format(i)+filename.split('.')[1],'w') as fw:
			fw.write(header)
			fw.writelines(each)

# document operations
def make_az(filename, data, header, layout, testing=False, **az_args):  ## az file to do remake instead of using gt1 file run on crosscore
	# az file for backup/remakes, from data
	#with open((Dirs.stage if testing else Dirs.az_line+'Target GT\\')+filename+'.txt','w') as az_file:
	with open((Dirs.stage if testing else Dirs.az_line)+filename+'-az.txt','w') as az_file:
		az_file.write(header)
		for seq, record in enumerate(data, 1):
			record_info = copy.deepcopy(record)
			record_info['filename'] = filename
			record_info.update(az_args)
			az_file.write(layout.format(seq=seq, asterisk='*' if seq%5==0 else '', **record_info))

def make_machine(filename, data, layout, **machine_args):
	with open(Dirs.stage+filename,'w') as machine:
		for seq, record in enumerate(data, 1):
			record_info = copy.deepcopy(record) # copy the value only not the ref location
			record_info['filename'] = filename
			record_info.update(machine_args)
			machine.write(layout.format(seq=seq, **record_info))

def make_proofs(filename, data, layout_card, layout_wrap, layout_label, **proof_args):
	with open(Dirs.stage+filename+' - card proof.txt','w') as cp, open(Dirs.stage+filename+' - wrap proof.txt','w') as wp, open(Dirs.stage+filename+' - label proof.txt','w') as lp:
		for record in (0, 1, -3, -2, -1):
			record_info = copy.deepcopy(data[record])
			record_info.update(proof_args)

			record_info['acctmasked'] = '{acct-1} {acct-2:.2}XX XXXX {acct-4}'.format(**data[record])
			record_info['track1masked'] = data[record]['track1'][:7] + 'XXXXXX' + data[record]['track1'][13:]
			record_info['track2masked'] = data[record]['track2'][:6] + 'XXXXXX' + data[record]['track2'][12:]
			if 'card_exp' in record_info.keys(): record_info['card_exp'] = 'Card Expires '+data[record]['exp']
			record_info['asterisk'] = '*' if record==-1 else ''
		
			cp.write(layout_card.format(**record_info))
			wp.write(layout_wrap.format(**record_info))
			lp.write(layout_label.format(**record_info))

def make_proofs_AMEX(filename, data, layout_card, layout_wrap, layout_label, **proof_args):
	with open(Dirs.stage+filename+' - card proof.txt','w') as cp, open(Dirs.stage+filename+' - wrap proof.txt','w') as wp, open(Dirs.stage+filename+' - label proof.txt','w') as lp:
		for record in (0, 1, -3, -2, -1):
			record_info = copy.deepcopy(data[record])
			record_info.update(proof_args)
			#1234 12xxxx x2345
			record_info['acctmasked'] = data[record]['acct465'][:7] + 'XXXX X' + data[record]['acct465'][13:]
			record_info['track1masked'] = data[record]['track1'][:7] + 'XXXXX' + data[record]['track1'][12:]
			record_info['track2masked'] = data[record]['track2'][:6] + 'XXXXX' + data[record]['track2'][11:]
			if 'card_exp' in record_info.keys(): record_info['card_exp'] = 'Card Expires '+data[record]['exp']
			record_info['asterisk'] = '*' if record==-1 else ''
		
			cp.write(layout_card.format(**record_info))
			wp.write(layout_wrap.format(**record_info))
			lp.write(layout_label.format(**record_info))

def make_zrecords_list(filename, data):
	# z record list file
	# ((zstack_qty+1) * 2) + ((zstack_qty+1) * ((qty / freq) - (1 if qty%freq==0 else 0)))
	total_zrecords = 0
	group_index = 0
	current_ctrl_number = None
	current_qty = 0
	zs_file_lines = []
	for record in data:
		if record['zrzp'] in ('ZR  ','  ZP'):
			total_zrecords += 1
			if current_ctrl_number is None:
				current_ctrl_number = record['ctrl_number']
				group_index += 1
				current_qty += 1
			else:
				if current_ctrl_number != record['ctrl_number']:
					zs_file_lines.append('{:0>5} - {} - {:>5}\n'.format(group_index, current_ctrl_number, current_qty))
					group_index += 1
					current_ctrl_number = record['ctrl_number']
					current_qty = 1
				else:
					current_qty += 1
	zs_file_lines.append('{:0>5} - {} - {:>5}\n'.format(group_index, current_ctrl_number, current_qty))
	with open(Dirs.stage+filename+'_Z Records List.txt','w') as zs_file:
		zs_file.write('List of Z record cards\nFilename: '+filename+'\n\nGroup - Serial Nmbr - Quantity\n')
		zs_file.writelines(zs_file_lines)
	return total_zrecords

def make_gt1(filename, data, headers, layout, **gt1_args):
	with open(Dirs.stage+filename+'.gt1','w') as machine:
		machine.write(('~'.join(headers)+'\n') if headers else '')
		for seq, record in enumerate(data, 1):
			record_info = copy.deepcopy(record)
			record_info.update(gt1_args)
			machine.write(layout.format(seq=seq, **record_info))

def make_1pass_org(filename, data, headers, layout, **pass1_args):
	with open(Dirs.stage+filename+'.txt','w') as machine:
		machine.write(('~'.join(headers)+'\n') if headers else '')
		for seq, record in enumerate(data, 1):
			record_info = copy.deepcopy(record)
			record_info.update(pass1_args)
			machine.write(layout.format(seq=seq, **record_info))

def make_1pass(filename, data, headers, layout, label_headers='', label_layout='', **cmd_args):
	with open(Dirs.stage+filename+'.txt','w') as machine:
		if label_headers:
			machine.write('~'.join(label_headers)+'\n')
			machine.write(label_layout.format(filename=filename,**cmd_args))


		machine.write(('~'.join(headers)+'\n') if headers else '')
		for seq, record in enumerate(data, 1):
			record_info = copy.deepcopy(record)
			record_info.update(cmd_args)
			machine.write(layout.format(seq=seq, **record_info))

def make_sn(filename, data, field_to_use):
	# sn.gt1.ald file (magic numbers or control numbers, from data with zrecords no stack, backwards)
	if field_to_use not in ('magic_number','ctrl_number'): raise Exception('Invalid field_to_use: '+field_to_use)
	with open(Dirs.stage+filename+'.sn.gt1.ald','w') as sn_file:
		sn_file.write('\n'.join([record[field_to_use] for record in data[::-1] if record['zrzp'] != 'ZR  '])+'\n')

def make_tc(filename, carrier_front, tc_part):
	# tc.gt1.ald file ('part front~T&C Part#', 10 lines only)
	with open(Dirs.stage+filename+'.tc.gt1.ald','w') as tc_file:
		for record in range(10):
			tc_file.write('{}~{}\n'.format(carrier_front, tc_part))

def make_whs(filename, data, multipack=False, cards_per_form=3):
	whs = Warehouse(Dirs.warehouse+filename+'.whs')
	if not multipack:
		whs.whs_header = strftime('{}.txt for {:,} rcds is OTN on %A - %B %d, %Y'.format(filename, len(data))).center(96)+'\n'
		whs.page_header = ('Search|        Ctrl No        |         '*2)+'\n'+('·'*96)+'\n'
		for seq, record in enumerate(data, 1): whs.add_line('{seq:0>6}       {ctrl_number:<27}'.format(seq=seq, **record))
		whs.format_data(59)
	else:
		whs.whs_header = strftime('File: {}.txt for {:,} cards, {:,} carriers is OTN on %A - %B %m, %Y').format(filename, len(data), len(data)/cards_per_form).center(96)+'\n'
		whs.page_header = ('Search|      Magic Number     |     Child Ctrl      |     Parent Ctrl     |       Ctrl')+'\n'+('·'*96)+'\n'
		for seq, record in enumerate(data, 1): whs.data.append('{seq:0>6}{magic_number:>17}{child_ctrl_number:>24}{parent_ctrl_number:>22}{ctrl_number:>21}\n'.format(seq=seq, **record))
		whs.format_data()
	whs.finish()

def make_report_setup(filename, job, job_info, multipack=False, **fields):
	report_config = ReportConfig(Dirs.pdf+filename+'.pdf', job.json_file)
	report_config.fields.update(fields)
	report_config.fields['filename'] = filename + ('' if not multipack else 'top.txt')
	report_config.transfer_fields()

	if multipack:
		job.reports['backup'].add_document(report_config)
		job.reports['inventory'].add_document(report_config)
		report_config.fields['filename'] = filename+'top'
		if report_config.fields['cardcode'] == 'blank-white':
			report_config.fields['cardcode'] = fields.get('cardcode_top','')
			report_config.fields['addcol2'] = fields.get('cardcode_mid','')
			report_config.fields['addcol3'] = fields.get('cardcode_bot','')
		job.reports['dailies'].add_document(report_config)
		job.reports['x3'].add_document(report_config)

	if not job_info['testing']: HSA_Database.add_to_database(report_config)
	if not multipack: job.add_to_reports(report_config)
	report_config.finish()

def add_to_label(label, ctrl_numbers, filename, jobname):
	label.acct_numbers = ctrl_numbers #list of control number
	label.update_totals()
	tray_values = label.calculate_layer1() #return a list of dic
	for row in range(label.layer1_total):
		label.data.append([
			filename,
			tray_values[row]['pans'],
			tray_values[row]['pane'],
			str(len(label.data)).zfill(6), #str(row+1).zfill(6),
			tray_values[row]['qty'],
			jobname
		])

def make_ctrl(filename, ctrl_numbers):
	with open(Dirs.return_files+filename+'_control numbers.txt','w') as ctrl_file:
		ctrl_file.write('\n'.join(ctrl_numbers)+'\n')

def make_cmd(filename, cmd_type, cmd_files, **cmd_args):
	if cmd_type not in ('incomm','target','incomm_scandiff'): raise Exception('Invalid cmd_type: '+cmd_type)
	cmd_files.add_line(Dirs.return_files+filename+'_command line.txt\n')
	#layout = vsp['cmd_layout_incomm'] if cmd_type=='incomm' else vsp['cmd_layout_target']
	if cmd_type=='incomm':
		layout = vsp['cmd_layout_incomm']
	elif cmd_type=='incomm_scandiff':
		layout = vsp['cmd_layout_incomm_scandiff']
	else:
		layout = vsp['cmd_layout_target']

	with open(Dirs.return_files+filename+'_command line.txt','w') as cmd_file:
		cmd_file.write(layout.format(**cmd_args))

def make_cn(filename, data, cn_type, cn_reference, **cn_args):
	# make an incomplete cn file and add the cn
	extensions = {'01': '_WhiteTests', '02': '_LiveSamples', '03': ''}

	if filename[-2:] not in ('01','02','03'): raise Exception('Invalid filename: '+filename)
	if cn_type.lower() not in ('greencard','greencardvms','vspto','multipack'): raise Exception('Invalid cn_type: '+cn_type)

	if cn_type.lower() in ('greencard','multipack'):
		cn_filename = strftime(vsp['cn_filename_greencard'].format(filename=filename, extension=extensions[filename[-2:]]))
		with open(Dirs.return_files+cn_filename,'w') as cn_file:
			cn_file.write(','.join(vsp['cn_headers_greencard'])+'\n')
			for record in data:
				record_info = copy.deepcopy(record)
				record_info.update(vsp['cn_info_greencard'])
				record_info.update(vsp['live_sample_info_greencard' if filename[-2:] in ('01','02') else 'prod_info_greencard'])
				record_info.update(cn_args)
				cn_file.write((vsp['cn_layout_greencard'] if cn_type.lower()=='greencard' else vsp['cn_layout_greencard_multipack']).format(**record_info))
				
	elif cn_type.lower() in ('greencardvms'):
		cn_filename = strftime(vsp['cn_filename_greencard'].format(filename=filename, extension=extensions[filename[-2:]]))
		with open(Dirs.return_files+cn_filename,'w') as cn_file:
			cn_file.write(','.join(vsp['cn_headers_greencardvms'])+'\n')
			for record in data:
				record_info = copy.deepcopy(record)
				record_info.update(vsp['cn_info_greencard'])
				record_info.update(vsp['live_sample_info_greencard' if filename[-2:] in ('01','02') else 'prod_info_greencard'])
				record_info.update(cn_args)
				#cn_file.write((vsp['cn_layout_greencard'] if cn_type.lower()=='greencard' else vsp['cn_layout_greencard_multipack']).format(**record_info))
				cn_file.write(vsp['cn_layout_greencardvms'].format(**record_info))

	else:
		cn_filename = strftime(vsp['cn_filename_vspto'].format(extension=extensions[filename[-2:]], **cn_args))
		with open(Dirs.return_files+cn_filename,'w') as cn_file:
			cn_file.write(','.join(vsp['cn_headers_vspto'])+'\n')
			for record in data:
				record_info = copy.deepcopy(record)
				record_info.update(vsp['cn_info_vspto'])
				record_info['date'] = strftime(record_info['date'])
				record_info.update(cn_args)
				cn_file.write(vsp['cn_layout_vspto'].format(**record_info))
	cn_reference.fields['cn_filename'] = cn_filename
	cn_reference.add_line()

class CN_Reference(TextFile):
	cn_reference_layout = '{filename},{bundle_start},{bundle_end},{master_start},{master_end},{pallet_start},{pallet_end},{description},{cn_filename},{order_id},{ffid}\n'
	fields = {
		'filename': '',
		'cn_filename': '',
		'bundle_start': '0000000',
		'bundle_end': '0000000',
		'master_start': '000000',
		'master_end': '000000',
		'pallet_start': '0000',
		'pallet_end': '0000',
		'order_id': '',
		'ffid': '',
		'description': ''
	}

	def __init__(self, out_filename):
		TextFile.__init__(self, out_filename)
		self.fields = copy.deepcopy(CN_Reference.fields)
		self.data.append('Filename,Bundle Start,Bundle End,Master Start,Master End,Pallet Start,Pallet End,Description,CN Filename,Order ID, FFID\n')

	def update_fields(self, **fields):
		self.fields.update(fields)

	def add_line(self):
		self.data.append(CN_Reference.cn_reference_layout.format(**self.fields))
		self.fields = copy.deepcopy(CN_Reference.fields)

# report operations
def update_rpt(filename, data_length, job, jobname, total_zrecords=0):
	job.reports['rpt'].add_line('{:<10} for {:>8,} records. {} - {}'.format(' ', data_length, jobname, filename) + (' ({:,} Z Records)\n'.format(total_zrecords) if total_zrecords else '\n'))
	job.reports['rpt'].cards += data_length

def main():
	# if multipack/UFAN, set encrypt to False, manually merge all files into one, keep the filename as the production return file, manually call encrypt_incomm_return
	import_to_bundler(encrypt=True)

if __name__ in '__main__':
	main()
