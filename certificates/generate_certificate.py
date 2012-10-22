# coding: utf-8

import argparse
import datetime
import os
import StringIO
import subprocess
import sys
import uuid

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.lib import colors 
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

def readFileAsString(filename):
    file = open(filename, "r")
    contents = file.read().decode("utf-8")
    file.close()
    return contents
    
def writeStringToFile(string, filename):
    ensure_dir(filename)
    file = open(filename, "w")
    file.write(string.encode("utf-8"))
    file.close()

def sign_pdf(pdf_path, destination_sig_path):
    # gpg --armor --output certificate.sig --detach-sig certificate.pdf
    ensure_dir(destination_sig_path)
    subprocess.call(["gpg", "--armor","--output", destination_sig_path, "--detach-sig", pdf_path])
    
    return readFileAsString(destination_sig_path)

def generate_verification_page(certificate, output_dir, grade = False):
    if grade:
        template_valid_page = readFileAsString("valid-graded.html")
    else:
        template_valid_page = readFileAsString("valid.html")
    template_verify_page = readFileAsString("verify.html")
    
    certificate_id = certificate['graded_certificate_id'] if grade else certificate['certificate_id']
    
    generated_path = certificate['graded_generated_path'] if grade else certificate['generated_path']
    download_url = certificate['graded_download_url'] if grade else certificate['download_url']
    
    signature_filename = os.path.basename(generated_path) + ".sig"
    signature_generated_path = os.path.join(output_dir, certificate_id, signature_filename)
    signature_download_url = "https://verify.edxonline.org/verify/{0}/{1}".format(certificate_id, signature_filename)
    
    
    signature = sign_pdf(generated_path, signature_generated_path)    
    
    new_valid_page = template_valid_page.format(NAME=certificate['name'], 
                                                CERTIFICATE_ID=certificate_id, 
                                                GRADE=certificate['grade'],
                                                SIGNATURE=signature)
    writeStringToFile( new_valid_page, os.path.join(output_dir, certificate_id, "valid.html") )
    
    
    new_verify_page = template_verify_page.format(NAME=certificate['name'],
                                                SIG_URL = signature_download_url,
                                                SIG_FILE = os.path.basename( signature_download_url ),
                                                PDF_FILE = os.path.basename( download_url ))
    writeStringToFile( new_verify_page, os.path.join(output_dir, certificate_id, "verify.html") )
                                                

template_pdf = None

def generate_certificates(student_name, certificate_id, filename, grade = None):
    """
    This method generates a certificate. If download_id is not specified, it is generates as a UUID4. It creates
    the file in /download_id/6002x-certificate-student_id.pdf.
    """
    
    # We make the template a global, because it is expensive to read
    global template_pdf
    
    if not template_pdf:
        #Open and load the template pdf
        template_pdf = PdfFileReader(file("certificate-template.pdf", "rb"))
        
    #This file is overlaid on the template certificate
    overlay_pdf_buffer = StringIO.StringIO()
    c = canvas.Canvas(overlay_pdf_buffer)
    
    #Import the fonts we need
    def fontpath(name):
        return os.path.join('fonts', name)

    pdfmetrics.registerFont( TTFont("Arial Unicode", fontpath('Arial Unicode.ttf')) )
        
    pdfmetrics.registerFont( TTFont("Baskerville", fontpath('Baskerville.ttf')) )  
    pdfmetrics.registerFont( TTFont("Baskerville-Bold", fontpath('Baskerville-bold.ttf')) )
    pdfmetrics.registerFont( TTFont("Baskerville-Italic", fontpath('Baskerville-Italic.ttf')) )
    pdfmetrics.registerFont( TTFont("Baskerville-BoldItalic", fontpath('Baskerville-BoldItalic.ttf')) )

    addMapping('Baskerville', 0, 0, 'Baskerville')    #normal
    addMapping('Baskerville', 0, 1, 'Baskerville-Italic')    #italic
    addMapping('Baskerville', 1, 0, 'Baskerville-Bold')    #bold
    addMapping('Baskerville', 1, 1, 'Baskerville-BoldItalic')    #italic and bold


    # Test with the paragraph object
    stylesheet=getSampleStyleSheet()
    normalStyle = stylesheet['Normal']

    styleBaskervileCentered = ParagraphStyle(name="baskervileCentered", 
                                            alignment=TA_CENTER, 
                                            fontName="Baskerville",
                                            fontSize=8,
                                            leading=14,
                                            textColor=colors.Color(0.462745,0.462745,0.462745))


    ######
    paragraph_string = "A course of study offered by <b><i>MITx</i></b> , an online learning initiative of <br/>" + \
                        "MASSACHUSETTS INSTITUTE OF TECHNOLOGY, through <b><i>edX</i></b>, <br/>" + \
                        "the online learning initiative of Harvard University and MIT"

    paragraph = Paragraph(paragraph_string, styleBaskervileCentered)

    paragraph.wrapOn(c, 11*inch, 8.5 * inch)
    paragraph.drawOn(c, 0, 3.62 * inch)

    ######
    styleBaskervileCentered.leading=12
    styleBaskervileCentered.fontSize=8

    paragraph_string = "<font color='0.266,0.266,0.266'>W. Eric L. Grimson</font>, Interim Dean of Online Education, <i>MITx</i><br/>" + \
                        "JUNE 12<super><font size=6>TH</font></super>, 2012"

    paragraph = Paragraph(paragraph_string, styleBaskervileCentered)

    paragraph.wrapOn(c, 11*inch, 8.5 * inch)
    paragraph.drawOn(c, 0, 2.15 * inch)


    ######
    styleBaskervileCentered.leading=9.8
    styleBaskervileCentered.fontSize=8

    paragraph_string = "HONOR CODE CERTIFICATE<br/>" + \
                        "*Authenticity of this certificate can be verified at <a href='https://verify.edxonline.org/cert/{0}'>https://verify.edxonline.org/cert/{0}</a>"
    paragraph_string = paragraph_string.format( certificate_id )
        
    paragraph = Paragraph(paragraph_string, styleBaskervileCentered)

    paragraph.wrapOn(c, 11*inch, 8.5 * inch)
    paragraph.drawOn(c, 0, 1.09 * inch)


    ######
    styleBaskervileCentered.leading=11.75
    styleBaskervileCentered.fontSize=10
    styleBaskervileCentered.textColor=colors.Color(0.266,0.266,0.266)
        
    if grade:
        paragraph_string = "This is to certify that<br/><br/><br/>" + \
                        "has earned a passing grade of {0} in successfuly completing <i>Circuits and Electronics 6.002x</i> "
        paragraph_string = paragraph_string.format( grade )
    else:
        paragraph_string = "This is to certify that<br/><br/><br/>" + \
                        "has successfully completed <i>Circuits and Electronics 6.002x</i> "

    paragraph = Paragraph(paragraph_string, styleBaskervileCentered)

    paragraph.wrapOn(c, 11*inch, 8.5 * inch)
    paragraph.drawOn(c, 0, 4.45 * inch)

    ######
    #This font doesn't have all of unicode. "Arial Unicode" does, but doesn't look as nice.
    c.setFont("Baskerville-Bold", 16)
    c.setFillColorRGB(0.266,0.266,0.266) 
    c.drawCentredString(11*inch/2, 4.71*inch, student_name)
    
    c.showPage()
    c.save()
        
    # Merge the overlay with the template, then write it to file
    output = PdfFileWriter()
    overlay = PdfFileReader( overlay_pdf_buffer )
        
    # We need a page to overlay on. So that we don't have to open the template
    # several times, we open a blank pdf several times instead (much faster)
    blank_pdf = PdfFileReader(file("blank.pdf", "rb"))

    final_certificate = blank_pdf.getPage(0)
    final_certificate.mergePage(template_pdf.getPage(0))
    final_certificate.mergePage(overlay.getPage(0))

    output.addPage(final_certificate)
    
    ensure_dir( filename )
    
    outputStream = file(filename, "wb")
    output.write(outputStream)
    outputStream.close()


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
        
def timeStamped(fname, fmt='{fname}_%Y-%m-%d-%H-%M-%S'):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

def generate_all_certificates(ungenerated_certificates, output_folder):
    """
    This takes information from find_passing_students.ungenerated_certificates() and gets it suitable
    to pass to generate_certificates. It just creates two entries for each certificate that needs the graded
    and ungraded generated
    """
    
    generated_certificates = {}
    
    counter = 0
    for certificate in ungenerated_certificates:
        name = certificate['name']
        certificate_id = certificate['certificate_id']
        if not certificate_id or len(certificate_id) != 32:
            certificate_id = random_uuid()
        graded_certificate_id = certificate['graded_certificate_id']
        if not graded_certificate_id or len(graded_certificate_id) != 32:
            graded_certificate_id = random_uuid()
        grade = certificate['grade']
        
        filename = "6002x_Certificate-{0}.pdf".format(certificate['user_id'])
        def download_url(certificate_id, filename):
            return "https://s3.amazonaws.com/verify.edxonline.org/dowload/{0}/{1}".format(certificate_id, filename)
        
        output_id = random_uuid()
        graded_output_id = random_uuid()
        
        output_name = os.path.join(output_folder, output_id, filename)
        graded_output_name = os.path.join(output_folder, graded_output_id, filename)
        
        generate_certificates(name, certificate_id, filename = output_name )
        generate_certificates(name, graded_certificate_id, filename = graded_output_name, grade = grade)
        
        generated_info = certificate.copy()
        generated_info.update({'download_url' : download_url(output_id, filename),
                                'generated_path' : output_name,
                                'graded_download_url' : download_url(graded_output_id, filename),
                                'graded_generated_path' : graded_output_name,
                                'certificate_id' : certificate_id,
                                'graded_certificate_id' : graded_certificate_id})
        
        generated_certificates[certificate['id']] = generated_info
        
        counter +=1
        
        if counter % 50 == 0:
            print str(datetime.datetime.now()), "Generated the certificates for" , counter , "students"
            
    print "Finished generating certificates!"
    return generated_certificates
    

def generate_all_verifies(generated_certificates, output_dir):
    for generatedCertificate_id in generated_certificates:
        certificate = generated_certificates[generatedCertificate_id]
        
        generate_verification_page(certificate, output_dir, grade = False)
        generate_verification_page(certificate, output_dir, grade = True)
    
    return generated_certificates
   
uuid_list = [] 
uuid_list_index = 0
def random_uuid():
    global uuid_list
    global uuid_list_index
    
    if uuid_list_index >= 0:
        if uuid_list_index < len(uuid_list):
            uuid_list_index += 1
            return uuid_list[uuid_list_index - 1]
        else:
            uuid_list_index = -1
            print "Ran out of supplied UUIDs. Now serving them from uuid library"
    return uuid.uuid4().hex
    
def main():
    global uuid_list
    input_data = None
    
    parser = argparse.ArgumentParser(description='Generate the certificates and verifcation pages for 6.002x.')
    parser.add_argument('-v', '--only-verify', action='store_true', help='Skip the generating pdfs step, only create the verify data. Input data MUST be the output of a previous run.')
    parser.add_argument('-g', '--only-generate', action='store_true', help='Only generate pdfs. Skip the verify step will be skipped. Input data MUST be from find_passing_students.ungenerated_certificates().')
    parser.add_argument('-u', '--uuids', type=argparse.FileType('r'), default=None)  #No default=sys.stdin
    parser.add_argument('-i', '--input-file', type=argparse.FileType('r'), default=None)  #No default=sys.stdin  
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    
    arguments = parser.parse_args()
    
    if arguments.input_file:
        in_file = arguments.input_file
        input_data_string = in_file.read()
        in_file.close()
        
        input_data = eval(input_data_string)
    else:
        print "No input data specified. Using test data."
        #This one is three certificate
        #input_data = [{'user_id': 1, 'name': u'Bridger Maxwell', 'grade': u'A', 'certificate_id': u'df9adafef59f4037bbc56722fbf3f088', 'enabled': False, 'download_url': None, 'graded_download_url': None, 'graded_certificate_id': u'e3c343fe7b5b4a308d4c5319be55108b', 'id': 1}, {'user_id': 2, 'name': u'Santa Claus', 'grade': u'B', 'certificate_id': u'440f117131584d2e9625ab2c562085bf', 'enabled': False, 'download_url': None, 'graded_download_url': None, 'graded_certificate_id': u'ec3b3b7c028b48ca987d03a837dcce5d', 'id': 2}, {'user_id': 3, 'name': u'Harry Potter', 'grade': u'B', 'certificate_id': u'6f893718d25a4121a6ded9731f78e1d4', 'enabled': False, 'download_url': None, 'graded_download_url': None, 'graded_certificate_id': u'8c863b45285d4e5d90a22f60c1199821', 'id': 3}]
    
        #This one is one certificate
        input_data = [{'user_id': 1, 'name': u'Bridger Maxwełł', 'grade': u'A', 'certificate_id': u'4f7c64dd3c284704b430a1a817b09a71', 'enabled': False, 'download_url': None, 'graded_download_url': None, 'graded_certificate_id': u'c792520fc0b949eebded6a791c0a51b4', 'id': 1}]
        
        # test_info_string = readFileAsString("/Volumes/NANO PRO/data")
        # input_data = eval(test_info_string) 
    
    if arguments.uuids:
        uuid_data = arguments.uuids.read()
        uuid_list = uuid_data.split("\n")
        uuid_list = filter( lambda x: len(x) == 32, uuid_list )
        print "Found" , len(uuid_list) , "uuids of length 32"
     
    if input_data:
        certificates_folder = timeStamped("certificates_generated")
        verify_folder = timeStamped("verify_generated")
        
        if not arguments.only_verify:
            input_data = generate_all_certificates(input_data, certificates_folder)
            
        if not arguments.only_generate:
            input_data = generate_all_verifies(input_data, verify_folder)
        
        arguments.outfile.write( str(input_data) )
        
if __name__ == "__main__":
    main()