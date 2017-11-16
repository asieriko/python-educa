import sys
import os
from PyQt5 import uic, QtWidgets, QtCore, QtGui

import numpy as np
import notakeb as notak
import database as db
import getEducaData as ged


class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.textName = QtWidgets.QLineEdit(self)
        self.textPass = QtWidgets.QLineEdit(self)
        self.textPass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)

    def handleLogin(self):
        if (self.textName.text() != '' and
            self.textPass.text() != ''):
            self.accept()
        else:
            QtGui.QMessageBox.warning(
                self, 'Error', 'Fill both the username and the password')



class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = uic.loadUi('notak.ui', self)
        self.ui.fileB.clicked.connect(self.selectdb)
        self.ui.updateDataB.clicked.connect(self.updatedata)
        self.ui.runB.clicked.connect(self.run)
        self.newYearCB.clicked.connect(self.newyear)
        self.outcsv = ""
        self.show()
        self.n = ''
        self.path = os.path.dirname(os.path.realpath(__file__))

    @QtCore.pyqtSlot()
    def selectdb(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Select Database file", "","sqlite3 files (*.db);;All Files (*)")
        print(fileName)
        if fileName:
            self.ui.dffileLE.setText(fileName)
            self.db = fileName
            self.data = db.database(self.db)
            self.years = self.data.get_years()
            self.ui.yearCB.addItems(sorted(self.years,reverse=True))
        #dialog for seleccting db

    @QtCore.pyqtSlot()
    def updatedata(self):
        year = self.ui.yearCB.currentText()
        #login = Login()
        #if login.exec_() == QtWidgets.QDialog.Accepted:
            #user = login.textName.text()
            #passwd = login.textPass.text()
            #try:
                #getdata = ged.GetEDUCAdata(user,passwd,verbose=False)
                #getdata.getallcurrentgrades()
                #self.data.delete_last_years_grades(year)
                #self.data.insert_grades([os.path.join(self.path,"grades"+year+".csv")])
            #except:
                #print("An error ocurred")
                #QtWidgets.QMessageBox.warning(self, 'An error ocurred', "An error ocurred while trying to update data, make sure that login data is correct", QtWidgets.QMessageBox.Ok)
        print(os.path.join(self.path,"grades"+year+".csv"))
        self.data.delete_last_years_grades(year)
        self.data.insert_grades([os.path.join(self.path,"grades"+year+".csv")])

    @QtCore.pyqtSlot()
    def newyear(self):
        year = max(self.years)
        ysplit = year.split("-")
        year = str(int(ysplit[0])+1)+"-"+str(int(ysplit[1])+1)
        print(year)
        login = Login()
        if login.exec_() == QtWidgets.QDialog.Accepted:
            user = login.textName.text()
            passwd = login.textPass.text()
            try:
                getdata = ged.GetEDUCAdata(user,passwd,verbose=False)
                getdata.getnamesyeardata2(year)
                self.data.insert_names([os.path.join(self.path,"names-year-"+year+".csv")])
                self.data.insert_yeardata([os.path.join(self.path,"names-year-"+year+".csv")])
            except:
                print("An error ocurred")
                QtWidgets.QMessageBox.warning(self, 'An error ocurred', "An error ocurred while trying to get new year's data, make sure that login data is correct", QtWidgets.QMessageBox.Ok)
        self.ui.yearCB.addItem(year) #Fixme: Insert in order

    @QtCore.pyqtSlot()
    def run(self):
        eb = self.ui.periodCB.currentText()
        ebn = self.ui.periodCB.currentIndex()
        year = self.ui.yearCB.currentText()
        ebaluaketak = [self.ui.periodCB.itemText(i) for i in range(self.ui.periodCB.count())]
        print(ebaluaketak,year,eb,ebn)
        ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA","Programa de Currículo Adaptado LOMCE"]
        dbhb=["1 ESO","2 ESO","3 ESO","4 ESO","1º Bach"]
        baliogabekokurtsoak = ucepca
        for lang in ['eu','es']:
            self.n = notak.notak(self.db,lang,debug=True)
            self.n.setWorkDir(eb+year)
            if eb == 'Final':
                self.n.generateFinalGrade()
            self.n.getData(year, ebaluaketak, ebn+1, baliogabekokurtsoak)

            if self.ui.coursePlotsEs.isChecked() and lang == 'es':
                print("course np.mean")
                self.n.generateCoursePlots(np.mean)
                print("course percent")
                self.n.generateCoursePlots(self.n.percent)
            if self.ui.coursePlotsEu.isChecked() and lang == 'eu':
                print("course np.mean")
                self.n.generateCoursePlots(np.mean)
                print("course percent")
                self.n.generateCoursePlots(self.n.percent)
            if self.ui.groupStatsPlotsEs.isChecked() and lang == 'es':
                taldeak = self.n.df[self.n.df.year == year].cgroup.unique()
                print("Group stats plots")
                for t in taldeak:
                    self.n.generateGroupStatsPlots(t)
            if self.ui.groupStatsPlotsEu.isChecked() and lang == 'eu':
                taldeak = self.n.df[self.n.df.year == year].cgroup.unique()
                print("Group stats plots")
                for t in taldeak:
                    self.n.generateGroupStatsPlots(t)
            if self.ui.allGroupStatsPlotsEs.isChecked() and lang == 'es':
                print("All group stats plots")
                self.n.generateAllGroupStatsPlots()
            if self.ui.allGroupStatsPlotsEu.isChecked() and lang == 'eu':
                print("All group stats plots")
                self.n.generateAllGroupStatsPlots()
            if self.ui.passPercentEs.isChecked() and lang == 'es':
                taldeak = self.n.df[self.n.df.year == year].cgroup.unique()
                print("Group pass percent")
                for t in taldeak:
                    self.n.generatePassPercent(ebaluaketak[ebn],year,t)
            if self.ui.passPercentEu.isChecked() and lang == 'eu':
                taldeak = self.n.df[self.n.df.year == year].cgroup.unique()
                print("Group pass percent")
                for t in taldeak:
                    self.n.generatePassPercent(ebaluaketak[ebn],year,t)
            if self.ui.allGroupPlotsEs.isChecked() and lang == 'eu':
                print("All group plots np.mean")
                self.n.generateAllGroupPlots(np.mean)
                print("All group plots n.percent")
                self.n.generateAllGroupPlots(self.n.percent)
            if self.ui.allGroupPlotsEs.isChecked() and lang == 'eu':
                print("All group plots np.mean")
                self.n.generateAllGroupPlots(np.mean)
                print("All group plots n.percent")
                self.n.generateAllGroupPlots(self.n.percent)
            if self.ui.promCoursePlotsEs.isChecked() and lang == 'es':
                print("course prom plots")
                self.n.promcourseplots(ebaluaketak[ebn])
            if self.ui.promCoursePlotsEu.isChecked() and lang == 'eu':
                print("course prom plots")
                self.n.promcourseplots(ebaluaketak[ebn])    
            if self.ui.bilingualCoursePlotsEs.isChecked() and lang == 'es':
                print("Bilingual plots")
                self.n.generateCourseBilvsCooursePlots(np.mean)
            if self.ui.bilingualCoursePlotsEu.isChecked() and lang == 'eu':
                print("Bilingual plots")
                self.n.generateCourseBilvsCooursePlots(np.mean)   
            if self.ui.courseStatsPlotsEs.isChecked() and lang == 'es':    
                print("Course stats plots")
                self.n.generateCourseStatsPlots()
            if self.ui.courseStatsPlotsEu.isChecked() and lang == 'eu':    
                print("Course stats plots")
                self.n.generateCourseStatsPlots()
            if self.ui.allStatsPlotsEs.isChecked() and lang == 'es':    
                print("generate All Stats Plots")
                self.n.generateAllStatsPlots()
            if self.ui.allStatsPlotsEu.isChecked() and lang == 'eu':    
                print("generate All Stats Plots")
                self.n.generateAllStatsPlots()
            if self.ui.allStatsStudentsEs.isChecked() and lang == 'es':
                print("generate Stats Student")
                self.n.generateStatsAllStudents(doc=True)
            if self.ui.allStatsStudentsEu.isChecked() and lang == 'eu':
                print("generate Stats Student")
                self.n.generateStatsAllStudents(doc=True)
            if self.ui.deptarmentPlotsEs.isChecked() and lang == 'es':
                print("Departaments plots")
                self.n.generateDeptPlots([np.mean,self.n.percent])
            if self.ui.deptarmentPlotsEu.isChecked() and lang == 'eu':
                print("Departaments plots")
                self.n.generateDeptPlots([np.mean,self.n.percent])
            if self.ui.primarySchoolsPlotsEs.isChecked() and lang == 'es':
                print("Primary School plots")
                self.n.generatePrymarySchoolPlots(np.mean)
            if self.ui.primarySchoolsPlotsEu.isChecked() and lang == 'eu':
                print("Primary School plots")
                self.n.generatePrymarySchoolPlots(np.mean)
    
        print("Mix askabi and EDUCA for the report")
        self.n.mergegroupstatsaskabi()    
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec_())
