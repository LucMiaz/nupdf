#compile using
# pyinstaller --onedir --onefile --name="nuPDF" --windowed gui.py
#
# for using an icon add
#  --icon='nuPDF.ico'

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QDialog, QCheckBox, QLineEdit, QListWidget, QApplication, QFileDialog, QHBoxLayout
from os import path, walk
from sys import exit
from rotatepdf import rotate_pages, merge_pdfs
boldfont=QFont("Arial",10)
boldfont.setBold(True)
normalfont =QFont("Arial",10)
normalfont.setBold(False)
class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        window = QWidget()
        main = QVBoxLayout()
        main.addWidget(QLabel('PDF manip'))
        layout = QVBoxLayout()
        """self.filetypes=QCheckBox('Get other file types?')
        self.filetypes.setChecked(False)
        main.addWidget(self.filetypes)"""
        self.selectFiles = QPushButton("Insert files")
        self.selectFiles.clicked.connect(self.getfiles)
        self.selectFiles.setFont(normalfont)
        main.addWidget(self.selectFiles)
        self.selectFolder = QPushButton("Insert folder")
        self.selectFolder.clicked.connect(self.getfolder)
        self.selectFolder.setFont(normalfont)
        main.addWidget(self.selectFolder)
        self.boxmerge=QCheckBox('Merge multiple files?')
        self.boxmerge.setChecked(True)
        self.boxmerge.setFont(normalfont)
        main.addWidget(self.boxmerge)
        self.bookmark=QCheckBox('Add bookmarks using file title?')
        self.bookmark.setChecked(True)
        self.bookmark.setFont(normalfont)
        main.addWidget(self.bookmark)
        self.recto_verso=QCheckBox('Recto verso ?')
        self.recto_verso.setChecked(False)
        self.recto_verso.setFont(normalfont)
        main.addWidget(self.recto_verso)
        self.same_file=QCheckBox('If recto verso, are they in two separate files?')
        self.same_file.setChecked(False)
        self.same_file.setFont(normalfont)
        main.addWidget(self.same_file)
        main.addWidget(QLabel('Rotation angle (clockwise)'))
        self.angle=QLineEdit('0')
        self.angle.setValidator(QIntValidator())
        self.angle.setAlignment(Qt.AlignRight)
        self.angle.setFont(normalfont)
        main.addWidget(self.angle)
        main.addWidget(QLabel('Pages to rotate (use - for range and ; for single pages, e.g. 1-2;5)'))
        self.pages=QLineEdit('')
        self.pages.setAlignment(Qt.AlignRight)
        self.pages.setFont(normalfont)
        main.addWidget(self.pages)
        self.setLayout(main)
        self.setWindowTitle('nuPDF')
        self.filenames = []
        self.listWidget = QListWidget()
        self.listWidget.setAcceptDrops(True)
        #Resize width and height
        self.listWidget.resize(300,120)
        self.listWidget.setWindowTitle('Files paths')
        self.listWidget.show()
        self.upBtn = QPushButton('Up', self)
        self.downBtn = QPushButton('Down', self)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.upBtn)
        self.buttonLayout.addWidget(self.downBtn)
        main.addLayout(self.buttonLayout)
        main.addWidget(self.listWidget)
        self.runbutton=QPushButton('Start')
        self.runbutton.setFont(normalfont)
        self.runbutton.clicked.connect(self.run)
        self.savingpath = QLineEdit()
        self.savingpath.setFont(normalfont)
        self.setsavingpath = QPushButton("Select saving path")
        self.setsavingpath.setFont(normalfont)
        self.setsavingpath.clicked.connect(self.savefile)
        self.empty=QPushButton('empty files list')
        self.empty.setFont(normalfont)
        self.empty.clicked.connect(self.empty_file_list)
        main.addWidget(self.empty)
        main.addWidget(self.setsavingpath)
        main.addWidget(self.savingpath)
        main.addWidget(self.runbutton)
        self.status = QLabel("Please select the files to work on and where to save the output")
        self.status.setFont(normalfont)
        self.upBtn.clicked.connect(self.upButton)
        self.downBtn.clicked.connect(self.downButton)
        main.addWidget(self.status)
    def upButton(self):
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
    def downButton(self):
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
    def empty_file_list(self):
        self.listWidget.clear()
        self.filenames = []
    def update_qlist(self):
        self.listWidget.clear()
        self.listWidget.addItems(self.filenames)
    def update_status(self):
        if len(self.filenames)>0 and self.savingpath!='':
            self.status.setText('Ready')
        elif len(self.filenames)>0 and self.savingpath=='':
            self.status.setText('Please insert a saving path')
        elif len(self.filenames)==0 and self.savingpath!='':
            self.status.setText('Please enter at least one file to work on')
        else:
            self.status.setText('Unknown error')
    def getfilesinfolder(self, folderpath):
        return [path.join(root, name)
                 for root, dirs, files in walk(folderpath)
                 for name in files
                 if name.endswith((".pdf", ".PDF", ".jpg",".jpeg",".gif",".GIF",".JPG",".JPEG",".raw",".RAW",".PNG",".png"))]
    def savefile(self):
        self.setsavingpath.setText("Select saving path")
        self.setsavingpath.setFont(normalfont)
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            path=dlg.selectedFiles()[0]
            self.savingpath.setText(path)
            if self.savingpath.text()[-4:]!='.pdf':
                path = self.savingpath.text()+".pdf"
                self.savingpath.setText(path)
        self.update_status()
    def getfiles(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFiles)
        if dlg.exec_():
            self.filenames += dlg.selectedFiles()
        self.update_qlist()
    def getfolder(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            filesInFolder = self.getfilesinfolder(dlg.selectedFiles()[0])
            self.filenames += filesInFolder
        self.update_qlist()

    def run(self):
        self.status.setText('Processing...')
        if self.savingpath.text()!="":
            self.runbutton.toggle()
            self.runbutton.setCheckable(False)
            if self.boxmerge.isChecked():
                merge=True
                path = self.savingpath.text()
            else:
                merge=False
                path = self.filenames[0]
            if self.bookmark.isChecked():
                bookmark = True
            else:
                bookmark = False
            pages_num=[]
            if self.angle.text() and int(self.angle.text())!=0:
                angle = int(self.angle.text())
            else:
                angle=0
            pages = self.pages.text()
            same_file = None
            if self.recto_verso.isChecked():
                recto_verso=True
                if self.same_file.isChecked():
                    same_file=True
            else:
                recto_verso = False
            if pages!="":
                from re import findall
                string=r'(([0-9]*)-([0-9]*))|([0-9]*(?![-]))'
                matches = findall(string, pages)
                for m in matches:
                    print(m)
                    if (m[1]!='' and m[2]!=''):
                        try:
                            pages_num+= range(int(m[1])-1,int([m[2]]))
                        except:
                            pass
                    elif m[3]!='':
                        try:
                            pages_num.append(int(m[3])-1)
                        except:
                            pass
            if merge:
                self.status.setText('Merging files...')
                merge_pdfs(self.filenames,self.savingpath.text(),recto_verso = recto_verso, same_file=same_file, bookmark = bookmark)
            if angle!=0:
                print(pages)
                print(pages_num)
                if len(pages_num)>0:
                    self.status.setText('Rotating pages %s ...' % ";".join([str(i) for i in pages_num]))
                    rotate_pages(path,self.savingpath.text(), pages=pages_num,angle=angle)
                else:
                    self.status.setText('Rotating all pages ...')
                    rotate_pages(path,self.savingpath.text(), angle=angle)
            self.status.setText('Done. File saved at %s' % self.savingpath.text())
            self.runbutton.toggle()
            self.runbutton.setCheckable(True)
            return self.runbutton
        else:
            self.setsavingpath.setText("**Select saving path**")
            self.setsavingpath.setFont(boldfont)
            self.update_status()
def main():
    app=QApplication([])
    app.setStyle('Fusion')
    ex=Form()
    ex.show()
    exit(app.exec_())

if __name__ == '__main__':
    main()
