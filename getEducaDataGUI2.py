import sys
from PyQt5 import uic, QtWidgets, QtCore, QtGui

from getEducaData import GetEDUCAdata

class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = uic.loadUi('geteducadata.ui', self)
        self.ui.browsefileb.clicked.connect(self.opencsvdir)
        self.ui.queryb.clicked.connect(self.query)
        self.outcsv = ""
        self.show()
        self.ged = GetEDUCAdata()

    @QtCore.pyqtSlot()
    def opencsvdir(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '/home/asier',"teachers.xml files (*teachers.xml)")
        self.saveto = fname[0]
        self.ui.savetole.setText(self.saveto)

    @QtCore.pyqtSlot()
    def query(self):
        print(self.ui.username.text(), self.ui.password.text())
        self.ged.setusername(self.ui.username.text())
        self.ged.setpassword(self.ui.password.text())
        self.ged.login()
        years = self.ged.getyears()
        self.ui.selectyearcb.clear()
        self.ui.selectyearcb.addItems([year[0] for year in reversed(years)])
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec_())        