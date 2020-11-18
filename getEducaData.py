import requests, os, json
import datetime
from bs4 import BeautifulSoup

'''
Obentern horarios
POST    https://educages.navarra.es/Educa/control/trGNRExportacion
txAction=conGHPHorarios&bFechaExportacion=F&bCursoEscolar=F&tbClases.txNombreCursoCorto=&tbClases.txNombreCurso=&tbClases.txNombreAsigCorto=&tbClases.txNombreAsig=&hdParams=&hdNombre=Horarios&iIdSede=1254&iIdCursoEscolar=132&idPRSPuesto=259911&rbIdiomaConsulta=eu&btnEnviar=Bidali

txAction	"conGHPHorarios"
bFechaExportacion	"F"
bCursoEscolar	"F"
tbClases.txNombreCursoCorto	""
tbClases.txNombreCurso	""
tbClases.txNombreAsigCorto	""
tbClases.txNombreAsig	""
hdParams	""
hdNombre	"Horarios"
iIdSede	"1254"
iIdCursoEscolar	"132"
idPRSPuesto	"259911"
rbIdiomaConsulta	"eu"
btnEnviar	"Bidali"

'''


class GetEDUCAdata():
    
    params = []
    years = []
    verbose = True

    def __init__(self, username="", password="", verbose=True):
        self.username = username
        self.password = password
        self.loginurl = "https://educages.navarra.es/Educa/control/ptrLogin" #Cambio a nuevo EDUCA "https://educages.navarra.es/acceso/login?service=https%3A%2F%2Feducages.navarra.es%2FEduca%2Fcontrol%2FptrLogin"
        self.profileurl = "https://educages.navarra.es/Educa/api/usuario/cambiarPerfil"
        self.coursesurl = "https://educages.navarra.es/Educa/control/trEVLExportacionCalificacionesDFCargaAjax"
        self.exporturl = "https://educages.navarra.es/Educa/control/trEVLExportacionCalificacionesDF"
        self.horariosurl = "https://educages.navarra.es/Educa/control/trGNRExportacion"
        self.horariosurl1 = "https://educages.navarra.es/Educa/control/trGNRExportacion?txAction=conGHPHorarios&txNombre=Horarios"
        self.guardiasurl = "https://educages.navarra.es/Educa/api/guardiasSustituciones/datosListadoGuardias?fechaInicio={}&fechaFin={}"
        self.sabanaurl = "https://educages.navarra.es/Educa/control/trEVLSabana?ViewType=XML"
        self.taldeakurl = "https://educages.navarra.es/Educa/control/trSelectionGrupoSede?bUsaSelectorCursoEscolar=T&txAction=trGHPHorarioGrupo?ViewType=XMLxsiOutputType=2"
        self.logouturl = "https://educages.navarra.es/Educa/public/Logout"
        self.path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data")
        self.s = requests.Session()
        self.body = {}
        self.lang = "eu"
        self.updatebody()
        self.verbose = verbose
        self.params = [['rbIdiomaConsulta',self.lang]]
        p = [['rbIdiomaConsulta',self.lang]]
        self.login()
        #self.params.append(['cbCursoEscolar',year[1]])

    def setusername(self, username):
        self.username = username
        self.updatebody()

    def setpassword(self, password):
        self.password = password
        self.updatebody()

    def setlang(self, lang):
        self.lang = lang

    def setfile(self, filepath):
        self.path = filepath

    def updatebody(self):
        self.body['username'] = self.username
        self.body['password'] = self.password
        self.params=[['rbIdiomaConsulta',self.lang]]

    def resetparams(self):
        self.params = self.p

    def options(self, soup, name):
        if self.verbose: 
            print(soup)
        keys = [str(x.text) for x in soup.find(id=name).find_all('option')]
        select = soup.find('select',{'name':name})
        option_tags = select.findAll('option')
        values = [option['value'].strip() for option in option_tags]
        return list(zip(keys,values))

    def login(self):
        if self.verbose: 
            print("Login in...")
        loginPage = self.s.get(self.loginurl)
        soup = BeautifulSoup(loginPage.text)
        #hiddenInputs = soup.findAll(name = 'input', type = 'hidden') #Cambio a nuevo EDUCA 
        #for hidden in hiddenInputs: #Cambio a nuevo EDUCA 
        #    name = hidden['name'] #Cambio a nuevo EDUCA 
        #    value = hidden['value'] #Cambio a nuevo EDUCA 
        #    self.body[name] = value #Cambio a nuevo EDUCA 
        form = soup.findAll(id='kc-form-login') #Cambio a nuevo EDUCA - nueva variable
        self.loginURL = form[0]['action'] #Cambio a nuevo EDUCA  - nueva variable
        r = self.s.post(self.loginURL, data = self.body) #Cambio a nuevo EDUCA  antes r = self.s.post(self.loginurl, data = self.body)
        if self.verbose: 
            print(self.body)
            print(self.s.headers)
        print("Login", r.status_code)
        payload = '103' #103 gestor - 101 profesor
        headers = {'content-type': 'application/json','Sec-Fetch-Site': 'same-origin','Sec-Fetch-Mode': 'cors'}
        r = self.s.post(self.profileurl,data=json.dumps(payload), headers=headers)
        if self.verbose: 
            print(self.body)
            print(self.s.headers)
        print("Profile Change", r.status_code)

    def logout(self):
        logoutPage = self.s.get(self.loginurl)
        if self.verbose: 
            print(self.s.headers)
            print("Loged out...")
        print("Logout ",logoutPage.status_code)
        
    def getyears(self):
        if self.verbose: 
            print("Querying years...")
        r = self.s.get(self.exporturl)
        print("Get years: ",r.status_code)
        soup = BeautifulSoup(r.text)
        years = self.options(soup,"cbCursoEscolar")
        return years

    def getcourses(self,year):
        if self.verbose: 
            print("Querying courses...")
        self.params = [['rbIdiomaConsulta','eu'],['cbCursoEscolar',year[1]]]
        r = self.s.post(self.coursesurl, data = self.params)
        print("Get Courses: ", r.status_code)
        soup = BeautifulSoup(r.text)
        courses = self.options(soup,"lbGrupos")
        return courses
    
    def selectcourses(self,courses):
        for course in courses:
            self.params.append(['lbGrupos',course[1]])
            if self.verbose: 
                print(course[1],course[0])
    
    def getsubjects(self):
        if self.verbose: 
            print("Querying subjects...")
        r = self.s.post(self.coursesurl, data = self.params)
        print("Get subjects: ",r.status_code)
        soup = BeautifulSoup(r.text)
        subjects = self.options(soup,"lbAsignaturas")
        return subjects
        
    def selectsubjects(self,subjects):
        for subject in subjects:
            self.params.append(['lbAsignaturas',subject[1]])
    
    def getpossibledata(self):
        matricula = "tbMatricula.ul"
        student = "tbAlumno.ul"
        grades = "tbCalificacionesDF.ul"
        finaldata = "tbDatosFinales.ul"
        data = ["tbMatricula.ul", "tbAlumno.ul", "tbCalificacionesDF.ul", "tbDatosFinales.ul"]
        if self.verbose: 
            print("Querying data...")
        datad = {}
        r = self.s.post(self.coursesurl, data = self.params)
        print("Get possible data: ",r.status_code)
        soup = BeautifulSoup(r.text)
        for opt in data:
            dat = self.getinputsid(soup, opt)
            datad[opt] = dat
        return datad
        
    def getinputsid(self, soup, name):
        if self.verbose: 
            print(soup)
            print(name)
        keys = [list([x['name'],x.parent.text.replace("\n","")]) for x in soup.find(id=name).find_all('input')]
        if self.verbose: print(keys)
        return keys
    
    def selectcustomdata(self,data):
        for param in data:
            self.params.append(["'"+param+"'",''])
    
    def selectgradedata(self,groupings=False): #Only grades
        self.params.append(['tbMatricula.txCursoEscolar',''])
        #no in new EDUCA self.params.append(['tbAlumno.txUsuarioUnico',''])
        self.params.append(['tbAlumno.txUsuarioEduca','']) #replaces uxuariounico in new educa
        self.params.append(['tbMatricula.txNombreCurso',''])
        if groupings:
            self.params.append(['tbMatricula.txNombreGrupo',''])
        self.params.append(['tbCalificacionesDF.nombreAsignatura',''])
        self.params.append(['tbCalificacionesDF.cursoAsignatura',''])
        self.params.append(['tbCalificacionesDF.evaluacion',''])
        self.params.append(['tbCalificacionesDF.calificacionNumericaOrd',''])        

    def selectyeardata(self):
        self.params.append(['tbMatricula.txCursoEscolar',''])
        self.params.append(['tbMatricula.txGrupoReferencia',''])
        self.params.append(['tbMatricula.txNombreGrupo',''])
        self.params.append(['tbMatricula.txTipoGrupo',''])
        self.params.append(['tbMatricula.txNombreCurso',''])
        self.params.append(['tbMatricula.txModLing',''])
        self.params.append(['tbAlumno.txNombreCompleto',''])
        #no in new EDUCA self.params.append(['tbAlumno.txUsuarioUnico',''])
        self.params.append(['tbAlumno.txUsuarioEduca','']) #replaces uxuariounico in new educa
        self.params.append(['tbMatricula.bRepite',''])

    def selectenddata(self):
        self.params.append(['tbMatricula.txCursoEscolar',''])
        #no in new EDUCA self.params.append(['tbAlumno.txUsuarioUnico',''])
        self.params.append(['tbAlumno.txUsuarioEduca','']) #replaces uxuariounico in new educa
        self.params.append(['tbDatosFinales.decTitulo',''])
        self.params.append(['tbDatosFinales.decPromocion',''])
        self.params.append(['tbMatricula.bEstado','']) #FIXME: Baja edo ez
        
    def selectpersonaldata(self):    
        #no in new EDUCA self.params.append(['tbAlumno.txUsuarioUnico',''])
        self.params.append(['tbAlumno.txUsuarioEduca','']) #replaces uxuariounico in new educa
        self.params.append(['tbAlumno.txNombreCompleto',''])
        self.params.append(['tbAlumno.cSexo',''])
        self.params.append(['tbAlumno.txNacionalidad',''])
        self.params.append(['tbAlumno.dtFechaNacimiento',''])
        
        
    def selecttimetabledata(self):    
        """
        <INPUT name="iIdSede" id="iIdSede" type="Hidden" value="1254"></INPUT>

        <INPUT name="iIdCursoEscolar" id="iIdCursoEscolar" type="Hidden" value="131"></INPUT>

        <INPUT name="idPRSPuesto" id="idPRSPuesto" type="Hidden" value="237949"></INPUT>
        """
        self.params.append(['txAction','conGHPHorarios'])
        self.params.append(['bFechaExportacion','F'])
        self.params.append(['bCursoEscolar','F'])
        self.params.append(['tbHorario.txSede',''])
        self.params.append(['tbHorario.txNombrePuesto',''])
        self.params.append(['tbHorario.txNombreProfesor',''])
        self.params.append(['tbHorario.dtFechaInicio',''])
        self.params.append(['tbHorario.dtFechaFin',''])
        self.params.append(['tbHorario.txParrilla',''])
        self.params.append(['tbHorario.iIdDiaSemana',''])
        self.params.append(['tbHorario.iHora',''])
        self.params.append(['tbHorario.txCuentaPNTEApps',''])
        #no in new EDUCA self.params.append(['tbAlumno.txUsuarioUnico',''])
        self.params.append(['tbAlumno.txUsuarioEduca','']) #replaces uxuariounico in new educa
        self.params.append(['tbClases.txGrupoAlumno',''])
        self.params.append(['tbClases.txNombreAula',''])
        self.params.append(['tbClases.txNombreCurso',''])
        self.params.append(['tbClases.txNombreAsigCorto',''])
        self.params.append(['tbClases.txNombreAsig',''])
        self.params.append(['hdParams',''])
        self.params.append(['hdNombre','Horarios'])
        self.params.append(['iIdSede','1254'])
        self.params.append(['iIdCursoEscolar','132'])#FIXME: hardcoded
        self.params.append(['idPRSPuesto','237949'])#FIXME: hardcoded
        self.params.append(['rbIdiomaConsulta',self.lang])
        self.params.append(['btnEnviar','Enviar'])

    def selectdata(self,data=[]):
        #self.params.append(['btnEnviar.x','43'])
        #self.params.append(['btnEnviar.y','10'])
        self.params.append(['btnEnviar','Bidali']) #Change in 2018-19 maybe for the new desing
        if "year" in data:
            self.selectyeardata()
        if "grades" in data:
            self.selectgradedata()
        if "gradesgroups" in data:
            self.selectgradedata(groupings=True)
        if "end" in data:
            self.selectenddata()
        if "personal" in data:
            self.selectpersonaldata()    
        

    def getdata(self,url,path=None):#def getdata(self,params,sesion?,path=None):
        if not path:
            path = os.path.join(self.path,"educa.csv")
        r = self.s.post(url, data=self.params)
        if self.verbose: 
            print(self.params)
            print(r.headers)
        print("Get data: ", r.status_code)
        print("Retrieveing data to file: " + path + "  ...")
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
                    
    def getallcurrentgrades(self,groupings=False):
        # self.login()
        years = self.getyears()
        courses = self.getcourses(years[-1]) #For most of the year
        #courses = self.getcourses(years[-2]) #At the end of the course, EDUCA has also next course data so current becomenes next...
        self.selectcourses(courses)
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        if groupings:
            self.selectdata(["gradesgroups"])
            rfile = os.path.join(self.path,"gradesgroups"+str(years[-1][0])+".csv")
        else:
            self.selectdata(["grades"])
            rfile = os.path.join(self.path,"grades"+str(years[-1][0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()

    def getallyeargrades(self,year):
        # self.login()
        years = self.getyears()
        for yearlist in years:
            if yearlist[0] == year:
                year = yearlist
        courses = self.getcourses(year)
        self.selectcourses(courses)
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        self.selectdata(["grades"])
        rfile = os.path.join(self.path,"grades"+str(year[0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()

        
    def getnamesyeardata(self,year=None):
        # self.login()
        if not year:
            years = self.getyears()
        else:
            years = [year] #FIXME: look at getallyeargrades
        courses = self.getcourses(years[-1])
        self.selectcourses(courses)
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        self.selectdata(["personal","year"])
        rfile = os.path.join(self.path,"names-year-"+str(years[-1][0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()


    def getnamesyeardata2(self,year=None):
        # self.login()
        years = self.getyears()
        if year:
            for y in years:
                if year==y[0]:
                    years=[y]
        print(y)
        courses = self.getcourses(years[-1])
        self.selectcourses(courses)
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        self.selectdata(["personal","year"])
        rfile = os.path.join(self.path,"names-year-"+str(years[-1][0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()

    def getnames4gradedata(self,year=None):
        # self.login()
        if not year:
            years = self.getyears()
        else:
            years = [year]  #FIXME: look at getallyeargrades
        courses = [["4º A","122391","es"],
            ["4º B","122392","es"],
            ["4º C","122393","es"],
            ["4º D","122394","es"],
            ["4 H","122395","eu"],
            ["4 I","122396","eu"],
            ["4 J","122397","eu"],
            ["4 K","122398","eu"]]
        for course in courses:
            self.params.append(['lbGrupos',course[1]])
        self.params.append(['cbCursoEscolar',years[-1][1]])
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        self.selectdata(["personal","grades"])
        rfile = os.path.join(self.path,"names-year"+str(years[-1][0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()

    def getnamesgroupgradedata(self,group,year=None):
        # self.login()
        if not year:
            years = self.getyears()
        else:
            years = [year]  #FIXME: look at getallyeargrades or getalldata
        self.params.append(['lbGrupos',group])
        self.params.append(['cbCursoEscolar',years[-1][1]])
        subjects = self.getsubjects()
        self.selectsubjects(subjects)
        self.getpossibledata()
        self.selectdata(["personal","grades"])
        rfile = os.path.join(self.path,"names-year-"+str(group)+"-"+str(years[-1][0])+".csv")
        self.getdata(self.exporturl,rfile)
        # self.logout()
    

    def gettimetabledata(self):
        # self.login()
        self.selecttimetabledata()
        rfile = os.path.join(self.path,"timetable.csv") #include year
        self.getdata(self.horariosurl,rfile)
        # self.logout()
    
    
    def getsabana(self,eb): #FIXME: Too hardcoded...
        periods = {"1. Ebaluazioa":"1","2. Ebaluazioa":"2","3. Ebaluazioa":"3","Azken Ebaluazioa":"4","Ohiz kanpoko Ebaluazioa":"5"}
        #"Ev inicial":"13" en la web
        taldeakHTML = self.s.get(self.taldeakurl)  #<- Current year only
        soup = BeautifulSoup(taldeakHTML.text)
        taldeak = self.options(soup,"cbGruposOrdinarios")
        groups = []
        for taldea in taldeak[1:]: #First element is the placeholder - Talde guztiak -
            if taldea[0] in ["PCA"]:
                continue
            elif taldea[0] in ["GELA ALTERNATIBOA","UCE"]:
                groups.append([taldea[1],taldea[0],"es"])
            elif taldea[0][-1] >= "H":
                groups.append([taldea[1],taldea[0],"eu"])
            else:
                groups.append([taldea[1],taldea[0],"es"])
        for group in groups:
            grupo = group[0]
            ev = periods[eb]
            name = group[1]
            lang = group[2]
            params = []
            params.append(['txRedirectLink','trEVLSabanaSelection?txxAction=trEVLSabana?ViewType=XML'])
            params.append(['ViewType','XML'])
            params.append(['txAction','trEVLSabana?ViewType=XML'])
            params.append(['cbGrupoAlumnos',grupo])
            params.append(['cbEvaluacionOrden',ev])
            params.append(['ckRecuperacion','on'])
            params.append(['ckEstadistica','on'])
            #params.append(['ckEvaluacionesAnteriores','on'])
            #params.append(['ckAsignaturasPendientes','on'])
            params.append(['txIdioma',lang])
            params.append(['btnEnviar','Enviar'])
            r = self.s.get(self.sabanaurl,data=params)
            print("Get sabana: ", r.status_code)
            if lang == "eu":
                path = os.path.join(self.path,name+"_Maindirea.pdf")
            else:
                path = os.path.join(self.path,name+"_Sábana.pdf")
            print("Retrieveing sabana to file: " + path + "  ...")
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content():
                        f.write(chunk)
    
    def getalldata(self,data,syear=None):
        # self.login()
        years = self.getyears()
        if syear:
            for y in years:
                if y[0] == syear:
                    years = [y]
        for year in years: #FIXME: if a year is selected, the for works??
            courses = self.getcourses(year)
            self.selectcourses(courses)
            subjects = self.getsubjects()
            self.selectsubjects(subjects)
            self.getpossibledata()
            self.selectdata([data])
            rfile = os.path.join(self.path,data+str(year[0])+".csv")
            self.getdata(self.exporturl,rfile)
        # self.logout()
        
    def getguards(self,date=None):
        # self.login()
        if date==None:
            date = datetime.datetime.now()
            date = date.strftime('%d/%m/%Y')
        r = self.s.get(self.guardiasurl.format(date,date))
        print(r.url)
        jsonresponse = json.loads(r.text)
        #print(j)
        guardias = jsonresponse["data"]["listadoInicial"]
        cantidad = len(guardias)
        todas = [[""] * 5 for i in range(cantidad)]
        for i in range(cantidad):
            if guardias[i]["estado"] in ["Anulada"]:
                continue
            print(guardias[i]["sesion"],end="-")
            print(guardias[i]["horaInicio"],end="-")
            print(guardias[i]["profesor"],end="-")
            print(guardias[i]["profesorSustituto"],end="-")
            grupos = "-".join([g["value"] for g in guardias[i]["grupos"]])
            asignaturas = "-".join([asig for asig in guardias[i]["asignaturas"]])
            aulas = "-".join([aula for aula in guardias[i]["aulas"]])
            print(guardias[i]["grupos"][0]["value"],grupos,end="-")
            print(guardias[i]["asignaturas"][0],end="-")
            print(guardias[i]["aulas"][0])
            todas[i] = [guardias[i]["sesion"],guardias[i]["horaInicio"],guardias[i]["profesor"],guardias[i]["profesorSustituto"],grupos,asignaturas,aulas]
            #{'idGSGuardia': 6191, 'idGSGuardiaEstado': 4, 'estado': 'Asignada', 'fecha': '18/12/2019', 'horaInicio': '13:35', 'horaFin': '14:30', 'sesion': 7, 'profesor': 'Asier Urio Larrea', 'puesto': 'TK_01', 'profesorSustituto': 'Irantzu Fernández Sáinz-de Murieta', 'idPFRProfesor': 79056, 'grupos': [{'id': 122395, 'value': '4 H'}], 'asignaturas': ['Tecnología ES4'], 'aulas': ['1_0C4'], 'idGSContabilidadGuardia': 0}
        
        # self.logout()
        return todas
        
if __name__ == "__main__":
    import getpass
    user = input("username: ")
    passwd = getpass.getpass()
    ged = GetEDUCAdata(user,passwd,verbose=False)
    t = ged.getguards()
    #ged.getnames4gradedata()
    #ged.getallcurrentgrades()
    ged.setfile("/home/asier/Hezkuntza/python-hezkuntza/python-educa/data")
    #ged.getalldata("personal","2016-2017")
    #print(ged.params)
    #ged.resetparams()
    #ged.getalldata("end","2016-2017")
    #ged.gettimetabledata()
    #ged.getallcurrentgrades(groupings=True)
    #print(ged.params)
    #ged.resetparams()
    #ged.getalldata("grades")
    ##print(ged.params)
    ##ged.resetparams()
    #ged.getalldata("end")
    #print(ged.params)
    #print("Done")
