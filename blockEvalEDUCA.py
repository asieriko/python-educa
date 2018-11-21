import requests, os
from bs4 import BeautifulSoup

class GetEDUCAdata():
    
    params = []
    verbose = True

    def __init__(self, username="", password="", verbose=True):
        self.username = username
        self.password = password
        self.loginurl = "https://educages.navarra.es/acceso/login?service=https%3A%2F%2Feducages.navarra.es%2FEduca%2Fcontrol%2FptrLogin"
        self.groupsURL = "https://educages.navarra.es/Educa/control/trSelectionGrupoAlumnosEvaluacion?iCtx=3&txAction=trEVLCierreEvaluacion"
        self.blockURL = "https://educages.navarra.es/Educa/control/trEVLCierreEvaluacion?txRedirectLink=https://educages.navarra.es/Educa/control/trEVLCierreEvaluacion?iIdGrupoAlumno={group}xsiIdEvaluacionOrden={period}xstxxRedirectLink=trSelectionGrupoAlumnosEvaluacion?txxxxAction=trEVLCierreEvaluacion&iIdGrupoAlumno={group}&iIdEvaluacionOrden={period}&txAction={action}"
        self.logouturl = "https://educages.navarra.es/Educa/public/Logout"
        self.s = requests.Session()
        self.body = {}
        self.lang = "eu"
        self.updatebody()
        self.verbose = verbose
        self.params = [['rbIdiomaConsulta',self.lang]]
        p = [['rbIdiomaConsulta',self.lang]]
        #self.params.append(['cbCursoEscolar',year[1]])

    def setusername(self, username):
        self.username = username
        self.updatebody()

    def setpassword(self, password):
        self.password = password
        self.updatebody()

    def setlang(self, lang):
        self.lang = lang


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
        hiddenInputs = soup.findAll(name = 'input', type = 'hidden')
        for hidden in hiddenInputs:
            name = hidden['name']
            value = hidden['value']
            self.body[name] = value
        r = self.s.post(self.loginurl, data = self.body)
        if self.verbose: 
            print(self.body)
            print(self.s.headers)
        print("Login", r.status_code)
        
    def logout(self):
        logoutPage = self.s.get(self.loginurl)
        if self.verbose: 
            print(self.s.headers)
            print("Loged out...")
        print("Logout ",logoutPage.status_code)
        
    def getgroups(self):
        if self.verbose: 
            print("Querying groups...")
        r = self.s.get(self.groupsURL)
        print("Get Groups: ", r.status_code)
        soup = BeautifulSoup(r.text)
        courses = self.options(soup,"iIdGrupoAlumno")
        return courses
    
    def blok(self,action="DESBLOQUEAR",period="1"):
        self.login()
        groupsList = self.getgroups()  # [g[1] for g in self.getgroups()]
        for group in groupsList:
            print(action,group[0],end="")
            url = self.blockURL.format(group=group[1],period=period,action=action)
            r = self.s.get(url)
            print(" Estado: ", "OK" if r.status_code == requests.codes.ok else " Error")
        self.logout()
        
        
if __name__ == "__main__":
    import getpass
    user = input("username: ")
    passwd = getpass.getpass()
    ged = GetEDUCAdata(user,passwd,verbose=False)
    ged.blok(action="BLOQUEAR",period="1")
    input("Presiona enter para DESBLOQUEAR")
    ged.blok(action="DESBLOQUEAR",period="1")
