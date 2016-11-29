import requests
import re
from bs4 import BeautifulSoup
from tkinter import *
import sys
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication
from PyQt5.QtGui import QIcon


class window(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    def initUI(self):               
        
        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)

        exitAction = QAction(QIcon('exit24.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exitAction)
        
        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Main window')    
        self.show()
        
        
class educaData():
    mainurl = 'https://educages.navarra.es/acceso/login?service=https%3A%2F%2Feducages.navarra.es%2FEduca%2Fcontrol%2FptrLogin'
    urlcourses = 'https://educages.navarra.es/Educa/control/trEVLExportacionCalificacionesDFCargaAjax'
    urlassistance = 'https://educages.navarra.es/Educa/control/trFAAsistenciaProfesor'
    urlexport = 'https://educages.navarra.es/Educa/control/trEVLExportacionCalificacionesDF'
    s = requests.Session()
    
    def options(self,soup,name):
        years = [str(x.text) for x in soup.find(id=name).find_all('option')]
        select = soup.find('select',{'name':name})
        option_tags = select.findAll('option')
        values = [option['value'].strip() for option in option_tags]
        return list(zip(years,values))

    def inputs(self,soup):
        name =  re.compile("infoFalta_falta")
        values = [x['value'].split("\",\"") for x in soup.find_all('input',{'name':name})]
        return values

    def start(self,username=None,password=None):
        body = {'username':username,'password':password}

        loginPage = self.s.get(self.mainurl)
        soup = BeautifulSoup(loginPage.text)
        hiddenInputs = soup.findAll(name = 'input', type = 'hidden')
        for hidden in hiddenInputs:
            name = hidden['name']
            value = hidden['value']
            body[name] = value

        r = self.s.post(self.mainurl, data = body)
        
    def getyears(self):
        a = self.s.get(self.urlexport).text
        soup = BeautifulSoup(a)
        years = self.options(soup,"cbCursoEscolar")
        return years #year = years[-1]

    def getcourses(self,year):
        params = {'rbIdiomaConsulta':'eu','cbCursoEscolar':year}
        r = self.s.post(self.urlcourses, data = params)
        soup = BeautifulSoup(r.text)
        courses = self.options(soup,"lbGrupos")
        return courses

    def getsubjects(self,year,courses):
        params=[]
        params.append(['rbIdiomaConsulta','eu'])
        params.append(['cbCursoEscolar',year[1]])

        for course in courses:
            params.append(['lbGrupos',course[1]])

        r = self.s.post(self.urlcourses, data = params)
        soup = BeautifulSoup(r.text)
        subjects = self.options(soup,"lbAsignaturas")
        return subjects

    def getdata(self,subjects):
        params = []
        for subject in subjects:
            params.append(['lbAsignaturas',subject[1]])
            
        params.append(['tbMatricula.txNumeroExpediente',''])    
        params.append(['rbIdiomaConsulta','eu'])
        params.append(['btnEnviar.x','43'])
        params.append(['btnEnviar.y','10'])
        r = self.s.post(self.urlexport, data = params)

    def getDayStudents(self, date):
       #a = self.s.get(self.urlexporot).text
       params = []
       params.append(['objectoJSONFaltasVuelta',''])
       params.append(['hdFecha',date]) #  19%2F03%2F2015
       params.append(['btnSeleccionar.x','54'])
       params.append(['btnSeleccionar.y','6'])
       r = self.s.post(self.urlassistance, data = params)
       soup = BeautifulSoup(r.text)
       values = self.inputs(soup)
       params = params + self.generateAttendance(values)
       for p in params:
         print(p)
      
    def generateAttendance(self,values):
      params = []
      c = [c for c in values]#.split("&quot;") if c not in ["[",",","]"]]
      for b in c:
         b[0] = b[0][2:]
         b[-1] = b[-1][:-2]
         d = "infoFalta_"+b[0]
         params.append([d,b])
      return params

class Application(Frame):
    
    ed = educaData()
    
    def start(self):
        self.ed.start()
        years = self.ed.getyears()
        print(years)
        self.years = StringVar()
        self.years.set("0") # initialize

        for year, code in years:
            self.y = Radiobutton(self, text=year,
                            variable=self.years, value=code,indicatoron=0,
                            command=self.courses)
            self.y.pack()

    def courses(self):
        print(self.years.get())
        courses = self.ed.getcourses(self.years.get())
        print(courses)
        self.courses = StringVar()
        self.courses.set("0")
        self.y.pack_forget()
        for course, code in courses:
            self.c = Radiobutton(self, text=course,
                            variable=self.courses, value=code,
                            command=self.subjects)
            self.c.pack()

    def subjects(self):
        print(self.courses.get())

    def createWidgets(self):
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"]   = "red"
        self.QUIT["command"] =  self.quit

        self.QUIT.pack({"side": "left"})

        self.hi_there = Button(self)
        self.hi_there["text"] = "Start",
        self.hi_there["command"] = self.start

        self.hi_there.pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

#root = Tk()
#app = Application(master=root)
#app.mainloop()
#root.destroy()

ed = educaData()
print("starting...")
ed.start(input("username"),input("password"))
print("started")
ed.getDayStudents("11/03/2015")
print("Students")
