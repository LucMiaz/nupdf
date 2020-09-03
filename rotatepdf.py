from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image
def read_path(path):
    try:
        pdf_reader = PdfFileReader(path)
    except:
        image1 = Image.open(path)
        im1 = image1.convert('RGB')
        path += ".pdf"
        im1.save(path)
        pdf_reader = PdfFileReader(path)
    return pdf_reader
def rotate_pages(path,savingpath, pages=None, angle = 90):
    pdf_writer = PdfFileWriter()
    pdf_reader = read_path(path)
    # Rotate page 90 degrees to the right
    number_of_pages = pdf_reader.getNumPages()
    if not pages:
        pages = [*range(0,number_of_pages)]
    for pagenum in [*range(0,number_of_pages)]:
        if pagenum in pages:
            if angle % 90 !=0:
                angle = 90 * int(angle/90)
            while angle <0:
                angle += 360
            while angle >360:
                angle -=360
            print("Rotate page by %s" % str(angle))
            page = pdf_reader.getPage(pagenum).rotateClockwise(angle)
        else:
            page = pdf_reader.getPage(pagenum)
        pdf_writer.addPage(page)
    with open(savingpath, 'wb') as fh:
        pdf_writer.write(fh)
def merge_pdfs(pdffiles, savingpath, recto_verso=False, same_file=None, bookmark = True):
    if len(pdffiles)>0:
        print('merging {}'.format(", ".join(pdffiles)))
        pdf_writer = PdfFileWriter()
        if same_file and same_file == True and recto_verso==True:
            recto_verso = False
        for path in pdffiles:
            pdf_reader = read_path(path)
            number_of_pages = pdf_reader.getNumPages()
            if recto_verso==True:
                print("recto_verso")
                #mixes half-half
                if number_of_pages % 2 == 0:# Even
                    recto = [*range(int(number_of_pages/2))]
                    verso = [*range(int(number_of_pages/2),number_of_pages)]
                else:# Odd
                    recto = [*range(int((number_of_pages+1)/2))]
                    verso = [*range(int((number_of_pages+1)/2),number_of_pages)]
                rng = []
                while len(recto)>0 or len(verso)>0:
                    if len(recto)>0:
                        rng.append(recto.pop(0))
                    if len(verso)>0:
                        rng.append(verso.pop(0))
            else:
                rng = range(number_of_pages)
            print(rng)
            pagenumber = pdf_writer.getNumPages()
            for pagenum in rng:
                page = pdf_reader.getPage(pagenum)
                pdf_writer.addPage(page)
            if bookmark:
                title = path.split("/")[-1].replace(".pdf","")
                pdf_writer.addBookmark(title = title, pagenum = pagenumber,
                color = (1,0.388,0.278))
        with open(savingpath,'wb') as fh:
            pdf_writer.write(fh)
        if same_file and same_file ==True:
            print('Filed merged, sorting for recto-verso now.')
            merge_pdfs([savingpath], savingpath, recto_verso=True, same_file=False, bookmark=bookmark)
        print('Merge done')
    else:
        print("No pdf file found. Abort.")
