import sys
import os
from PyQt5 import uic, QtWidgets, QtCore, QtGui

import numpy as np
import pandas as pd #for missingGradesPerTeacher
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
        self.ui = uic.loadUi('ui/notak.ui', self)
        self.ui.fileB.clicked.connect(self.selectdb)
        self.ui.updateDataB.clicked.connect(self.updatedata)
        self.ui.runB.clicked.connect(self.run)
        self.newYearCB.clicked.connect(self.newyear)
        self.cbEs.stateChanged.connect(self.enableEs)
        self.cbEu.stateChanged.connect(self.enableEu)
        self.outcsv = ""
        self.show()
        self.n = ''
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data")

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
            self.workDir = os.path.dirname(fileName)
            print(self.workDir)
        #dialog for seleccting db

    @QtCore.pyqtSlot()
    def updatedata(self):
        year = self.ui.yearCB.currentText()
        login = Login()
        if login.exec_() == QtWidgets.QDialog.Accepted:
            user = login.textName.text()
            passwd = login.textPass.text()
            try:
                getdata = ged.GetEDUCAdata(user,passwd,verbose=False)
                getdata.getallcurrentgrades()
                if self.cbMissingTeachers.isChecked() == True:
                    print("GetallCurrent and now with groupings")
                    getdata.getallcurrentgrades(groupings=True)
                    print("timetable")
                    getdata.gettimetabledata()
                    eb = self.ui.periodCB.currentText()
                    print("missing")
                    self.missingGradesPerTeacher(eb,year,"eu")
                if self.cbSheet.isChecked() == True:
                    print("Get Sheet")
                    eb = self.ui.periodCB.currentText()
                    getdata.getsabana(eb)
                getdata.logout()
                self.data.delete_last_years_grades(year)
                #move all downloaded data to  data/ and make a parameter in get...
                self.data.insert_grades([os.path.join(self.path,"grades"+year+".csv")])
            except:
                print("An error ocurred")
                QtWidgets.QMessageBox.warning(self, 'An error ocurred', "An error ocurred while trying to update data, make sure that login data is correct", QtWidgets.QMessageBox.Ok)

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
    def enableEs(self):
        if self.cbEs.isChecked() == True:
            self.ui.coursePlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.groupStatsPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.allGroupStatsPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.passPercentEs.setCheckState(QtCore.Qt.Checked)
            self.ui.allGroupPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.promCoursePlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.bilingualCoursePlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.courseStatsPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.allStatsPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.allStatsStudentsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.deptarmentPlotsEs.setCheckState(QtCore.Qt.Checked)
            self.ui.primarySchoolsPlotsEs.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.coursePlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.groupStatsPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allGroupStatsPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.passPercentEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allGroupPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.promCoursePlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.bilingualCoursePlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.courseStatsPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allStatsPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allStatsStudentsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.deptarmentPlotsEs.setCheckState(QtCore.Qt.Unchecked)
            self.ui.primarySchoolsPlotsEs.setCheckState(QtCore.Qt.Unchecked)

    @QtCore.pyqtSlot()
    def enableEu(self):
        if self.cbEu.isChecked() == True:
            self.ui.coursePlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.groupStatsPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.allGroupStatsPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.passPercentEu.setCheckState(QtCore.Qt.Checked)
            self.ui.allGroupPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.promCoursePlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.bilingualCoursePlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.courseStatsPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.allStatsPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.allStatsStudentsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.deptarmentPlotsEu.setCheckState(QtCore.Qt.Checked)
            self.ui.primarySchoolsPlotsEu.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.coursePlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.groupStatsPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allGroupStatsPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.passPercentEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allGroupPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.promCoursePlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.bilingualCoursePlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.courseStatsPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allStatsPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.allStatsStudentsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.deptarmentPlotsEu.setCheckState(QtCore.Qt.Unchecked)
            self.ui.primarySchoolsPlotsEu.setCheckState(QtCore.Qt.Unchecked)

    
    def missingGradesPerTeacher(self,period,year,lang):
        print("Generating missingGradesPerTeacher")
        timetable = os.path.join(self.path,"timetable.csv") #include year?
        grades = os.path.join(self.path,"gradesgroups"+year+".csv")
        import time
        timestr = time.strftime("%Y_%m_%d-%H_%M_%S")
        output = os.path.join(self.path,"jarrigabe_"+timestr+".csv")
        
        self.subject1= {'eu':'Irakasgaiaren Izena','es':'Nombre Asignatura'}
        self.group = {'eu':'Taldea','es':'Grupo'}
        self.subject2= {'eu':'Irakasgaia','es':'Asignatura'}
        self.teacher = {'eu':'Irakaslea','es':'Profesor'}
        self.grade = {'eu':'Zenbakizko nota ohikoa','es':'Nota numérica Ordinaria'}
        
        dfh = pd.read_csv(timetable,delimiter=";",encoding="ISO-8859-1")
        dfh.drop_duplicates(subset=[self.teacher[lang] ,self.subject2[lang],self.group[lang]],inplace=True)
        dfg = pd.read_csv(grades,delimiter=";",encoding="ISO-8859-1")
        dfg = dfg[dfg.Ebaluaketa==period]
        #falta da aktibo ez dauden irakasleak filtratzea
        dft = dfg.merge(dfh,left_on=[self.subject1[lang],self.group[lang]],right_on=[self.subject2[lang],self.group[lang]])

        def total(x):
            return int(len(x))


        def missing(x):
            print(x.isna().sum())
            return int(x.isna().sum())


        table = pd.pivot_table(dft,values=self.grade[lang],index=[self.teacher[lang],self.group[lang],self.subject2[lang]],aggfunc={total,missing})    
        table = table.astype({"total":int,"missing":int})
        table ['Ehunekoa'] = (table ['missing'] / table ['total']) *100
        table.to_csv(output,float_format='%.2f',decimal=',')
    
    
    @QtCore.pyqtSlot()
    def run(self):
        eb = self.ui.periodCB.currentText()
        ebn = self.ui.periodCB.currentIndex()
        year = self.ui.yearCB.currentText()
        ebaluaketak = [self.ui.periodCB.itemText(i) for i in range(self.ui.periodCB.count())]
        print(ebaluaketak,year,eb,ebn)
        ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA","Programa de Currículo Adaptado LOMCE","1-E.B.O.2 Aula Alternativa","2-E.B.O.2 Aula Alternativa"]
        dbhb=["1 ESO","2 ESO","3 ESO","4 ESO","1º Bach","1. DBH","2. DBH","3. DBH","4. DBH","3º Div.Cur.","4º Div.Cur.","4º Div. Cur.","1. Batxilergoa LOE","1. DBH LOMCE","1. Batxilergoa LOMCE","3. DBH LOMCE","3. Ikaskuntza eta Errendimendua Hobetzeko Programak","2. DBH LOMCE","4. DBH LOMCE","2. Ikaskuntza eta Errendimendua Hobetzeko Programak"]#,"2. Batxilergoa LOMCE",
        dbh12=["1. DBH LOMCE","2. DBH LOMCE"]
        Batx2 = ["2. Batxilergoa LOE","2. Batxilergoa LOMCE"]
        if self.ui.CbDBH1Batx.isChecked():
            baliogabekokurtsoak = ucepca+Batx2
        elif self.ui.CbBatx2.isChecked():
            baliogabekokurtsoak = ucepca+dbhb #+dbhb para solo 2bach
        else:
            baliogabekokurtsoak = ucepca
        print(baliogabekokurtsoak)
        for lang in ['eu','es']:
            self.n = notak.notak(self.db,lang,debug=False)
            self.n.setWorkDir(eb+year)            
            self.n.getData(year, ebaluaketak, ebn+1, baliogabekokurtsoak)
            if eb == 'Final':
                self.n.generateFinalGrade()
            
            mailak = self.n.df[self.n.df.year == year].course.unique()
            self.n.promcourseplots(ebaluaketak[ebn]) #Needed for groupstats.csv
            taldeak = self.n.df[self.n.df.year == year].cgroup.unique() #Needed for badsubjects.csv
            for t in taldeak:
                self.n.generatePassPercent(ebaluaketak[ebn],year,t)
            
            
            print("Course Pass Percentes")
            for m in mailak:
                self.n.generateCoursePassPercent(ebaluaketak[ebn],self.n.year,m)
            
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
            if self.ui.passPercentEs.isChecked() and lang == 'es': #Required before to generate pass percents
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
            if self.ui.allGroupPlotsEu.isChecked() and lang == 'eu':
                print("All group plots np.mean")
                self.n.generateAllGroupPlots(np.mean)
                print("All group plots n.percent")
                self.n.generateAllGroupPlots(self.n.percent)
            if self.ui.promCoursePlotsEs.isChecked() and lang == 'es': #Needed befor to gnerate grouptstats.csv
                print("course prom plots")
                self.n.promcourseplots(ebaluaketak[ebn])
            if self.ui.promCoursePlotsEu.isChecked() and lang == 'eu':
                print("course prom plots")
                self.n.promcourseplots(ebaluaketak[ebn])    
            if self.ui.bilingualCoursePlotsEs.isChecked() and lang == 'es':
                print("Bilingual plots")
                self.n.generateCourseBilPlots([np.mean,self.n.percent])
                self.n.generateCourseBilvsCooursePlots([np.mean,self.n.percent])
            if self.ui.bilingualCoursePlotsEu.isChecked() and lang == 'eu':
                print("Bilingual plots")
                self.n.generateCourseBilPlots([np.mean,self.n.percent])
                self.n.generateCourseBilvsCooursePlots([np.mean,self.n.percent])   
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
                
            print("generate reportgruoupdata.csv")
            self.n.generateGroupStats()
                
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
    
        #print("Mix askabi and EDUCA for the report")
        #self.n.generateGroupStats()    
        print("End of generation")
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec_())
