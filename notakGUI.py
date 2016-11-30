import sys
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication,QFileDialog,QMessageBox
from PyQt5.QtGui import QIcon

from notakeb import notak

class window(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):               
        
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        exitAction = QAction(QIcon.fromTheme('exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        openFile = QAction(QIcon.fromTheme('open'), 'Import', self)
        openFile.setShortcut('Ctrl+I')
        openFile.setStatusTip('Import from csv file')
        openFile.triggered.connect(self.importFileDialog)
        
        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)  
        fileMenu.addAction(exitAction)
                
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)
        
        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Academic Data Manager')    
        self.show()
        
        
    def importFileDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home/asier',"CSV data files (*.csv)")

        if fname[0]:
            f = open(fname[0], 'r')
            with f:
                data = f.read()
                self.textEdit.setText(data)    
            QMessageBox.information(self, "Success",
                                    "Successful import")
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = window()
    sys.exit(app.exec_())  