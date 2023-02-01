# This Python file uses the following encoding: utf-8
from Operations import Dirs
import reportlab, pyPdf, os, sys, shutil, json
from reportlab.graphics.barcode import code128

def makeReleaseSheet(out_filename, rsFields, newstamp=None):
	can = reportlab.pdfgen.canvas.Canvas(Dirs.pdf+'hold\\release_sheet_data.pdf', pagesize=reportlab.lib.pagesizes.letter)
	styles = reportlab.lib.styles.getSampleStyleSheet()

	if newstamp: # Only if reprinting
		ptext = """<font name = Times-Italic color=black size=11>%s</font>""" % newstamp
		createParagraph(can, ptext, 270, 602)

	for eachfield in rsFields:
		if rsFields[eachfield]['data'] == '': continue

		if eachfield == 'scanm' and rsFields['scanm']['data'] != '':
			pic = get_image(rsFields['scanm']['data'], width=12.37*reportlab.lib.units.cm)
			frame = reportlab.platypus.Frame(rsFields['scanm']['frame'][0]*reportlab.lib.units.cm,
											 rsFields['scanm']['frame'][1]*reportlab.lib.units.cm,
											 rsFields['scanm']['frame'][2]*reportlab.lib.units.cm,
											 rsFields['scanm']['frame'][3]*reportlab.lib.units.cm)
			if frame.add(pic,can) == 0:
				print 'Image {} is too large. Check image/frame dimensions.\n'.format(os.path.basename(rsFields['scanm']['data']))
				sys.exit()
			
		elif eachfield == 'barcodeString' and rsFields['barcodeString']['data'] != '':
			barcode128 = code128.Code128(rsFields['barcodeString']['data'],
										barHeight = float(rsFields['barcodeString']['barHeight'])*reportlab.lib.units.cm,
										barWidth = float(rsFields['barcodeString']['barWidth']))
			barcode128.drawOn(can, rsFields['barcodeString']['barLoc'][0], rsFields['barcodeString']['barLoc'][1])
			ptext = '<font name={font name} color={color} size={size}>{data}</font>'.format(data=rsFields['barcodeString']['data'], **rsFields['barcodeString']['text'])
			createParagraph(can, ptext, rsFields['barcodeString']['barText'][0], rsFields['barcodeString']['barText'][1])

		else:
			text = '<para align={align}><font name={font name} color={color} size={size}>{data}</font></para>'.format(
				align='right' if eachfield=='prg' else 'left', data=rsFields[eachfield]['data'], **rsFields[eachfield]['text'])
			line = reportlab.platypus.Paragraph(text, styles['Normal'])
			frame = reportlab.platypus.Frame(rsFields[eachfield]['frame'][0]*reportlab.lib.units.cm,
											 rsFields[eachfield]['frame'][1]*reportlab.lib.units.cm,
											 rsFields[eachfield]['frame'][2]*reportlab.lib.units.cm,
											 rsFields[eachfield]['frame'][3]*reportlab.lib.units.cm)
	
			# No need to add else statement, it will automatically try to add string to frame
			if frame.add(line,can) == 0:
				print 'Warning - {} was truncated for {}\n'.format(eachfield, os.path.basename(out_filename))
				while frame.add(line,can) == 0:
					if len(rsFields[eachfield]['data']) == 0:
						print 'Check frame dimensions / text size. Cannot fit {} into frame.\n'.format(eachfield)
						break
					rsFields[eachfield]['data'] = rsFields[eachfield]['data'][:-1].strip()
					text = '<para align={align}><font name={font name} color={color} size={size}>{data}</font></para>'.format(
						align='right' if eachfield=='prg' else 'left', data=rsFields[eachfield]['data']+'..', **rsFields[eachfield]['text'])
					line = reportlab.platypus.Paragraph(text, styles['Normal'])
					frame = reportlab.platypus.Frame(rsFields[eachfield]['frame'][0]*reportlab.lib.units.cm,
													 rsFields[eachfield]['frame'][1]*reportlab.lib.units.cm,
													 rsFields[eachfield]['frame'][2]*reportlab.lib.units.cm,
													 rsFields[eachfield]['frame'][3]*reportlab.lib.units.cm)
	can.save()

	template = pyPdf.PdfFileReader(open(Dirs.references+'ReleaseSheetTemplate.pdf','rb'))
	pdf_data = pyPdf.PdfFileReader(open(Dirs.pdf+'hold\\release_sheet_data.pdf','rb'))

	output = pyPdf.PdfFileWriter()
	page = template.getPage(0)
	page.mergePage(pdf_data.getPage(0))
	output.addPage(page)

	outputStream = open(out_filename,'wb')
	output.write(outputStream)
	outputStream.close()

def makeShipDetail(out_filename, sdFields, newstamp=None):
	can = reportlab.pdfgen.canvas.Canvas(Dirs.pdf+'hold\\ship_detail_data.pdf', pagesize=reportlab.lib.pagesizes.letter)
	styles = reportlab.lib.styles.getSampleStyleSheet()

	if newstamp: # Only if reprinting
		ptext = """<font name = Times-Italic color=black size=13>%s</font>""" % newstamp
		createParagraph(can, ptext, 30, 735)

	for eachfield in sdFields:
		if sdFields[eachfield]['data'] == '': continue
			
		if eachfield == 'barcodeString' and sdFields['barcodeString']['data'] != '':
			barcode128 = code128.Code128(sdFields['barcodeString']['data'], 
										barHeight = float(sdFields['barcodeString']['barHeight'])*reportlab.lib.units.cm, 
										barWidth = float(sdFields['barcodeString']['barWidth']))
			barcode128.drawOn(can, sdFields['barcodeString']['barLoc'][0], sdFields['barcodeString']['barLoc'][1])
			ptext = '<font name={font name} color={color} size={size}>{data}</font>'.format(data=sdFields['barcodeString']['data'], **sdFields['barcodeString']['text'])
			createParagraph(can, ptext, sdFields['barcodeString']['barText'][0], sdFields['barcodeString']['barText'][1])

		else:
			text = '<para align={align}><font name={font name} color={color} size={size}>{data}</font></para>'.format(
				align='left', data=sdFields[eachfield]['data'], **sdFields[eachfield]['text'])
			line = reportlab.platypus.Paragraph(text, styles['Normal'])
			frame = reportlab.platypus.Frame(sdFields[eachfield]['frame'][0]*reportlab.lib.units.cm,
											 sdFields[eachfield]['frame'][1]*reportlab.lib.units.cm,
											 sdFields[eachfield]['frame'][2]*reportlab.lib.units.cm,
											 sdFields[eachfield]['frame'][3]*reportlab.lib.units.cm)
	
			# No need to add else statement, it will automatically try to add string to frame
			if frame.add(line,can) == 0: 
				print 'Warning - {} was truncated for {}\n'.format(eachfield, os.path.basename(out_filename))
				while frame.add(line,can) == 0:
					if len(sdFields[eachfield]['data']) == 0:
						print 'Check frame dimensions / text size. Cannot fit {} into frame.\n'.format(eachfield)
						break
					sdFields[eachfield]['data'] = sdFields[eachfield]['data'][:-1].strip()
					text = '<para align={align}><font name={font name} color={color} size={size}>{data}</font></para>'.format(
						align='left', data=sdFields[eachfield]['data']+'..', **sdFields[eachfield]['text'])
					line = reportlab.platypus.Paragraph(text, styles['Normal'])
					frame = reportlab.platypus.Frame(sdFields[eachfield]['frame'][0]*reportlab.lib.units.cm,
													 sdFields[eachfield]['frame'][1]*reportlab.lib.units.cm,
													 sdFields[eachfield]['frame'][2]*reportlab.lib.units.cm,
													 sdFields[eachfield]['frame'][3]*reportlab.lib.units.cm)
	can.save()

	template = pyPdf.PdfFileReader(open(Dirs.references+'ShipDetailTemplate.pdf','rb'))
	pdf_data = pyPdf.PdfFileReader(open(Dirs.pdf+'hold\\ship_detail_data.pdf','rb'))

	output = pyPdf.PdfFileWriter()
	page = template.getPage(0)
	page.mergePage(pdf_data.getPage(0))
	output.addPage(page)

	outputStream = open(out_filename,'wb')
	output.write(outputStream)
	outputStream.close()

def combinePages(out_file_name, pages=[], delete_files=True):
	#pages = an array of [paths\to\pdf]

	output = pyPdf.PdfFileWriter()

	for eachpage in pages:
		page_to_append = open(eachpage, 'rb')
		append_pdf(pyPdf.PdfFileReader(page_to_append),output)
		output.write(open(out_file_name,'wb'))
		page_to_append.close()

		if delete_files: os.remove(eachpage)
		else: shutil.move(eachpage, Dirs.default+os.path.basename(eachpage))

def createParagraph(c, text, x, y):
	style = reportlab.lib.styles.getSampleStyleSheet()
	width, height = reportlab.lib.pagesizes.letter
	p = reportlab.platypus.Paragraph(text, style=style["Normal"])
	p.wrapOn(c, width, height)
	p.drawOn(c, x, y, reportlab.lib.units.mm)

def append_pdf(input,output):
	[output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

def get_image(path, width=1*reportlab.lib.units.cm):
	img = reportlab.lib.utils.ImageReader(path)
	iw, ih = img.getSize()
	aspect = ih / float(iw)
	return reportlab.platypus.Image(path, width=width, height=(width * aspect))

if __name__ in '__main__':
	pass
