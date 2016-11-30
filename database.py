# -*- coding: utf-8 -*-
# from __future__ import division
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
from _collections import defaultdict

class database:

    def __init__(self, db, lang='es'):
        """
        Initiates the class
        :param db: the sqlite3 db file path
        :return: None
        """
        self.db = db
        self.csv_periods = []
        self.subjectsavg = defaultdict(defaultdict)
        #importing student data
        self.csv_educa = {'eu':'Usuario EDUCA','es':'Usuario EDUCA'}
        self.csv_uniquename = {'eu':'Erabiltzaile izen bakarra','es':'Nombre de usuario único'}  # FIXME es names
        self.csv_fullname = {'eu':'Izen Osoa','es':'Nombre Completo'}
        self.csv_birthday = {'eu':'JaiotegunaFecha','es':'Nacimiento'}
        self.csv_nationality = {'eu':'Nazionalitatea','es':'Nacionalidad'}
        #FIXME: self.csv_gender = {'eu':'','es':''}
        #Still not using them:
        self.csv_birthplace_es = {'eu':'Jaioterria (ES)','es':'Localidad Nacimiento (ES)'}
        self.csv_birthplace_eu = {'eu':'Jaioterria (EU)','es':'Localidad Nacimiento (EU)'}
        self.csv_birthcountry_es = {'eu':'Jaiotze-herrialdea (ES)','es':'País Nacimiento (ES)'}
        self.csv_birthcountry_eu = {'eu':'Jaiotze-herrialdea (EU)','es':'País Nacimiento (EU)'}
        #importing year data for each student
        self.csv_year = {'eu':'Ikasturtea','es':'Curso Escolar'}
        self.csv_course = {'eu':'Kurtso','es':'Curso matrícula'}
        self.csv_ref_group = {'eu':'Erreferentzia-taldea','es':'Grupo ordinario de referencia'}
        self.csv_lang = {'eu':'Hizkuntza eredua','es':'Modelo lingüístico'}
        self.csv_repeating = {'eu':'Errepikatzen du','es':'Repite'}
        self.csv_promoting = {'eu':'Promozioa','es':'Promoción'}
        #Still not using them:
        self.csv_group_type = {'eu':'Talde mota','es':'Tipo de grupo'}
        self.csv_group = {'eu':'Taldea','es':'Grupo'}
        #These two to improve promoting row, its one or the other or none? (for the current course), never both
        self.csv_degree_decision = {'eu':'Tituluaren gaineko erabakia','es':'Decisión sobre el título'}
        self.csv_promoting_decicision = {'eu':'Kurtsoz igotzearen gaineko erabakia','es':'Decisión sobre la promoción'}
        #Importing subjects, and grades, (year and name already defined)
        self.csv_period = {'eu':'Ebaluaketa','es':'Evaluación'}
        self.csv_subject_name = {'eu':'Irakasgaiaren Izena','es':'Nombre Asignatura'}
        self.csv_subject_course = {'eu':' Irakasgaiaren Kurtsoa','es':'Curso de la asignatura'}
        self.csv_subject_type = {'eu':'Irakasgaiaren mota','es':'Tipo de la Asignatura'}
        self.csv_grade = {'eu':'Zenbakizko nota ohikoa','es':'Nota numérica Ordinaria'}
        #Importing subjects,abreviations, course and dept The file from EDUCA shoulb be edited!
        self.csv_subjname_eu = {'eu':'IRAKASGAIA','es':'IRAKASGAIA'}
        self.csv_subjname_es = {'eu':'ASIGNATURA','es':'ASIGNATURA'}
        self.csv_abv_es = {'eu':'ASIGNATURA_CORTO','es':'ASIGNATURA_CORTO'}
        self.csv_abv_eu = {'eu':'IRAKAS_MOTZA','es':'IRAKAS_MOTZA'}
        self.csv_subjcourse = {'eu':'CURSO_CORTO','es':'CURSO_CORTO'}
        self.csv_dept = {'eu':'DEPT','es':'DEPT'}
        self.csv_subjgroup  = {'eu':'TALDE','es':'TALDE'}
        self.csv_stage = {'eu':'ETAPA_CORTO','es':'ETAPA_CORTO'}
        self.csv_code = {'eu':'CODE','es':'CODE'}

        #{'eu':'','es':''} Others...




    def configure(self, year, periods, unekoeb=1, excludedCourses=[], baliogabekolaburdurak=[]):
        """
        Configures course and group ploting
        :param year: The year whose marks will be plotted
        :param periods: Evaluative period list
        :param unekoeb: Current period as int (as index+1 for the list)
        :param excludedCourses: Courses that won't generate a plot
        :param baliogabekolaburdurak: Abreviations that won't generate a plot
        :return:
        """
        self.csv_year = year
        self.csv_periods = periods
        #self.excludedCourses = [str(ec.decode()) for ec in excludedCourses]
        self.excludedCourses =  excludedCourses
        notcourses = "NOT results.course = '" + ("' AND NOT results.course = '").join(
            excludedCourses) + "'"  # The query works if excludedCourses = []
        notabreviations = "NOT abreviations.course = '" + (
        "' AND NOT  abreviations.course = '").join(
            baliogabekolaburdurak) + "'"  # The query works if baliogabekolaburdurak = []
        self.ebnumber = unekoeb
        if self.ebnumber > len(self.csv_periods):
            print("Error: ebnumber > eb kopurua")

        ebselect = "results.period = '" + ("' OR results.period = '").join(
            self.csv_periods[:self.ebnumber]) + "'"
        con = sqlite3.connect(self.db)
        self.df = pd.read_sql("SELECT *, abreviations.course as subjcourse "
                              "FROM results INNER JOIN  abreviations ON results.subject=abreviations.name "
                              "WHERE  (" + ebselect + ") "
                              "AND (" + notcourses + ") "
                              "AND (" + notabreviations + ") "
                              "AND NOT (results.grade='')",
                              con)
        con.close()
        self.df.drop(['id', 'name'], inplace=True, axis=1)
        self.df.grade = self.df.grade.astype(int)
        self.df['lang'] = self.df['language'].map(self.modelo)
        self.df['coursename'] = self.df.iloc[:, 2].map(self.csv_coursecopy)
        self.df['coursenumber'] = self.df.iloc[:, 2].map(self.csv_coursenumber)
        # iragazi beharko litzateke ere aurreko urteko pendienteak if coursenumber != subjcourse
        # df=df.rename(columns={'coursename':'course'})
        # df=df[df['subjcourse'] == df['subjcourse']]
        self.df = self.df.drop('course', axis=1)

    def generate_names_table(self):
        """
        Generates the database for storing the the names and their codes
        :return:
        """
        con = sqlite3.connect(self.db)
        con.execute('''CREATE TABLE names
            (uniquename TEXT PRIMARY KEY NOT NULL,
            educa           TEXT   NOT NULL,
            fullname        TEXT NOT NULL,
            birthday	TEXT,
            gender	TEXT,
            nationality	TEXT,
            primaryschool	TEXT);''')
        print("names table created successfully")
        con.close()

    def generate_yeardata_table(self):
        """
        Generates the database for storing the students situation each course
        :return:
        """
        con = sqlite3.connect(self.db)
        con.execute('''CREATE TABLE yeardata
            (id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            uniquename  TEXT   NOT NULL,
            year        TEXT NOT NULL,
            course      TEXT NOT NULL,
            cgroup      TEXT NOT NULL,
            lang        TEXT NOT NULL,
            repeating   INTEGER NOT NULL,
            promoting   TEXT,
            unique(uniquename,year));''')
        print("yeardata table created successfully")
        con.close()


    def generate_grade_table(self,cur=None):
        """
        Generates the database for storing the information
        about students's  grades
        :return:
        """
        con = sqlite3.connect(self.db)
        con.execute('''CREATE TABLE grades
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            year           TEXT   NOT NULL,
            uniquename        TEXT  NOT NULL,
            subject        TEXT  NOT NULL,
            course         TEXT NOT NULL,
            period        TEXT  NOT NULL,
            grade         INTEGER);''')
        print("Grades table created successfully")
        con.close()

    def generate_abreviations_table(self, cur=None):
        """
        Generates the database for storing the information
        about subjects: Their names, and relations
        :return:
        """
        con = sqlite3.connect(self.db)
        con.execute('''CREATE TABLE abreviations
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            stage          TEXT   NOT NULL,
            code          TEXT   NOT NULL,           
            subject_group  TEXT,
            name_es           TEXT   NOT NULL,
            name_eu           TEXT   NOT NULL,
            abv_es        TEXT NOT NULL,
            abv_eu        TEXT  NOT NULL,
            course        INT NOT NULL,
            dept           TEXT NOT NULL);''')
        print("Abreviations table created successfully")
        con.close()

    def generate_all_tables(self):
        """
        Generates all database tables:
        names
        yeardata
        abreviations
        grades
        """
        self.generate_names_table()
        self.generate_yeardata_table()
        self.generate_abreviations_table()
        self.generate_grade_table()

    def insert_names(self, files):
        '''
        :param files: A list of csv files with the following format:
        Izen Osoa,Usuario EDUCA,Erabiltzaile Izen Bakarra
        ['Urio Larrea, Asier', '654asdfa', 'auriolar']
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='names'").fetchall()[0][
            0] == 0:
            self.generate_names_table(cur)
        for file in files:#FIXME Try catch?
            print(file)
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                uniquename = self.get_csv_header_index(headers,self.csv_uniquename)
                educa = self.get_csv_header_index(headers,self.csv_educa)
                fullname = self.get_csv_header_index(headers,self.csv_fullname)
                birthday = self.get_csv_header_index(headers,self.csv_birthday)
                gender = self.get_csv_header_index(headers,self.csv_gender)
                nationality = self.get_csv_header_index(headers,self.csv_nationality)
                print(fullname)
                for row in reader:
                    cur.execute(
                        "INSERT OR IGNORE INTO names(uniquename, educa, fullname, birthday, gender, nationality) VALUES(?, ?, ?, ?, ?, ?)",
                        (row[uniquename], row[educa], row[fullname],row[birthday], row[gender], row[nationality]))
        con.commit()
        con.close()

    def insert_yeardata(self, files):
        '''
        :param files: A list of csv files with the following format:
        Izen Osoa,Usuario EDUCA,Erabiltzaile Izen Bakarra
        ['Urio Larrea, Asier', '654asdfa', 'auriolar']
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='yeardata'").fetchall()[0][
            0] == 0:
            self.generate_years_table(cur)
        for file in files:#FIXME Try catch?
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                uniquename = self.get_csv_header_index(headers,self.csv_uniquename)
                year = self.get_csv_header_index(headers,self.csv_year)
                course = self.get_csv_header_index(headers,self.csv_course)
                group = self.get_csv_header_index(headers,self.csv_ref_group)
                lang = self.get_csv_header_index(headers,self.csv_lang)
                repeating = self.get_csv_header_index(headers,self.csv_repeating)
                promoting = self.get_csv_header_index(headers,self.csv_promoting)
                for row in reader:
                    cur.execute(
                        "INSERT INTO yeardata(uniquename, year, course, cgroup, lang, repeating, promoting) VALUES(?, ?, ?,?, ?, ?, ?)",
                        (row[uniquename], row[year], row[course], row[group], row[lang], row[repeating], row[promoting]))
        con.commit()
        con.close()
    
    def update_primaryschool_data(self,files):
        '''
        :param files: A list of csv files with the following format:
        
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='names'").fetchall()[0][
            0] == 0:
            #FIXME: ERROR!  
            self.generate_names_table(cur)
        for file in files:#FIXME Try catch?
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                uniquename = self.get_csv_header_index(headers,self.csv_uniquename)
                #FIMXE primaryschool = self.get_csv_header_index(headers,self.csv_primaryschool)
                for row in reader:
                    cur.execute(
                        "UPDATE names SET primaryschool =? WHERE uniquename=?",
                        (row[primaryschool],row[uniquename]))
        con.commit()
        con.close()
    
    
    def update_promotion_data(self,files):
        '''
        :param files: A list of csv files with the following format:
        Izen Osoa,Usuario EDUCA,Erabiltzaile Izen Bakarra
        ['Urio Larrea, Asier', '654asdfa', 'auriolar']
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='yeardata'").fetchall()[0][
            0] == 0:
            #FIXME: ERROR!  
            self.generate_years_table(cur)
        for file in files:#FIXME Try catch?
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                uniquename = self.get_csv_header_index(headers,self.csv_uniquename)
                year = self.get_csv_header_index(headers,self.csv_year)
                promoting = self.get_csv_header_index(headers,self.csv_promoting)
                for row in reader:
                    cur.execute(
                        "UPDATE yeardata SET promoting=? WHERE uniquename=? AND year=?",
                        (row[promoting],row[uniquename], row[year]))
        con.commit()
        con.close()

    def insert_abreviatons(self, file):
        '''
        :param file: A file with the following format:
        Subject,LAB,ABR,course
        Arte eta Teknologia Esparrua 1,ATE,AAT,1
        :return None
        ''' #FIXME
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='abreviations'").fetchall()[0][0] == 0:
            self.generate_abreviations_table(cur)
        with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=",")
                headers = next(reader, None)  # get first row with headers
                subjname_eu = self.get_csv_header_index(headers,self.csv_subjname_eu)
                subjname_es = self.get_csv_header_index(headers,self.csv_subjname_es)
                abv_eu = self.get_csv_header_index(headers,self.csv_abv_eu)
                abv_es = self.get_csv_header_index(headers,self.csv_abv_es)
                subjcourse = self.get_csv_header_index(headers,self.csv_subjcourse)
                subject_group = self.get_csv_header_index(headers,self.csv_subjgroup)
                stage = self.get_csv_header_index(headers,self.csv_stage)
                code = self.get_csv_header_index(headers,self.csv_code)
                dept = "changeme" #FIXMEself.get_csv_header_index(headers,self.csv_dept)
                for row in reader:
                    subject_group_value = ''
                    if row[subject_group] != '':
                            subject_group_value = row[subject_group]
                    cur.execute("INSERT INTO abreviations(stage,code,subject_group,name_eu,name_es, abv_eu, abv_es, course, dept) VALUES(?, ?, ?, ?, ?, ?)",
                        (row[stage],row[code],subject_group_value,row[subjname_eu], row[subjname_es], row[abv_eu], row[abv_es], row[subjcourse], dept))#row[dept]))
        con.commit()
        con.close()

    def insert_grades(self, files):
        '''
        :param files: A list of csv files with the following format:
        Ikasturtea,Taldea,Kurtso,Hizkuntza eredua,Izen Osoa,Irakasgaiaren Izena,Ebaluaketa,Zenbakizko nota ohikoa
        ['2013-2014', '1. I', '1. DBH', 'D', 'XXXXX', 'Gizarte Zientziak, Geografia eta Historia BH1', '2. Ebaluaketa', '9']
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='grades'").fetchall()[0][
            0] == 0:
            self.generate_grade_table(cur)
        for file in files:
            print(file)
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                print(headers)
                year = self.get_csv_header_index(headers,self.csv_year)
                uniquename = self.get_csv_header_index(headers,self.csv_uniquename)
                subject = self.get_csv_header_index(headers,self.csv_subject_name)
                course = self.get_csv_header_index(headers,self.csv_subject_course)
                period = self.get_csv_header_index(headers,self.csv_period)
                grade = self.get_csv_header_index(headers,self.csv_grade)
                try:
                    for row in reader:
                        print(row)
                        if row[grade] != '':
                            grade_value = int(row[grade])
                        else:
                            grade_value = ''
                        cur.execute(
                            "INSERT INTO grades(year, uniquename, subject, course, period, grade) VALUES(?, ?, ?, ?, ?, ?)",
                            (row[year], row[uniquename], row[subject], row[course], row[period], grade_value))
    #                        (row[year], row[uniquename], self.get_subject_id(row[subject]), row[course], row[period], grade_value)) #FIXME Create the other table
                except Exception as inst:
                       print(type(inst))    # the exception instance
                       print(inst.args)     # arguments stored in .args
                       print(inst) 
        con.commit()
        con.close()

    def update_primaryschool(self, files):
        '''
        new function to add primary school for existing sutdents
        This information is not in EDUCA so they have to send it
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()

        print("Opened database successfully")
        for file in files:
            with open("/home/asier/Hezkuntza/python-hezkuntza/Python-educa/data/eskolak.csv", 'r', encoding="UTF-8") as results:
                reader = csv.reader(results, delimiter=";")
                headers = next(reader, None)  # get first row with headers
                print(headers)
                for row in reader:
                    print(row)
                    cur.execute(
                        "UPDATE names SET primaryschool = ? WHERE uniquename = ?",
                        (row[1], row[0]))
                
        con.commit()
        con.close()  

    def get_csv_header_index(self,header,valuedic):
        print(header,valuedic)
        for k in valuedic.keys():
            if valuedic[k] in header:
                return header.index(valuedic[k])
        raise ValueError(valuedic," not found")

    #@memoize
    def get_subject_id(self, subject):
        """
        Gets a subjects id in abreiatons table
        """#FIXME some cache??
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        subject_id = cur.execute("select id from abreviations where name_es = :subject or name_eu = :subject", {"subject": subject}).fetchone()[0]
        con.close()
        if subject_id:
            return subject_id
        raise ValueError


    def get_subjects(self,cur=None):
        """
        Gets all subjects stored in the database
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        subjects = cur.execute("select distinct subject from results").fetchall()
        for subject in subjects:
            print((subject[0]))
        return [s[0] for s in subjects]

    def get_years(self):
        """
        Gets all years stored in the database
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        years = cur.execute("select distinct year from results").fetchall()
        for year in years:
            print((year[0]))
        return [a[0] for a in years]

    def get_courses(self, year=None, student=None):
        """
        Gets all years stored in the database
        :param year: Year of wich courses will be returned
        :param student: Student of whose courses will be returned
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        sql = "select distinct course from results"
        if year:
            sql = sql + " where year='" + year + "'"
        if student:
            sql = sql + " where student='" + student + "'"
        courses = [c[0] for c in cur.execute(sql).fetchall() if c[0].encode("utf8") not in self.excludedCourses]
        for course in sorted(courses):
            print(course)
        return courses


    def get_cascading(self,years=None,lang=None):
        """
        Gets all courses, if year and lang provided
        If years not provided returns years
        if lang not provided but years is returns lang
        :return:
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        if not years:
            years = cur.execute("select distinct year from yeardata").fetchall()
            con.close()
            return {'years':[a[0] for a in years]}
        if not lang:
            lang = cur.execute("select distinct lang from yeardata where (year='"+"' OR year='".join(year)+"')").fetchall()
            con.close()
            return {'years':years, 'lang':[a[0] for a in lang]}
        courses = cur.execute("select distinct course from yeardata where (year='"+"' OR year='".join(year)+"') AND (lang='"+"' OR lang='".join(lang)+"')").fetchall()
        con.close()
        return {'years':years, 'lang':lang,'courses':[a[0] for a in courses]}

    def get_promotion_stats(self,year=None,course=None,lang=None):
        """
        Returns promotion data and its relation with course repeating
        params should be lists
        without parameters: SELECT repeating, promoting, count('uniquename') FROM yeardata  GROUP BY repeating,promoting
        with year: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE year='2011-2012' GROUP BY repeating,promoting
        with course: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE course ='1. DBH' GROUP BY repeating,promoting
        with lang: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE lang ='D' GROUP BY repeating,promoting
        with year and course: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE year='2011-2012' AND  course ='1. DBH' GROUP BY repeating,promoting
        with year and lang: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE year='2011-2012' AND  lang ='D' GROUP BY repeating,promoting
        with lang and course: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE course ='1. DBH' AND  lang ='D' GROUP BY repeating,promoting
        SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE (course='2. Batxilergoa LOE') AND (lang='A' OR lang='G') GROUP BY repeating,promoting
        with lang, year and course: SELECT repeating, promoting, count('uniquename') FROM yeardata WHERE year='2011-2012' AND  course ='1. DBH' AND  lang ='D' GROUP BY repeating,promoting
        """
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        conditions = []
        select = "SELECT repeating, promoting, count('uniquename') FROM yeardata "
        where = ""
        groupby = " GROUP BY repeating,promoting"
        sql = select + where + groupby
        if year:
            conditions += ["(year='"+"' OR year='".join(year)+"')"]
        if course:
            conditions += ["(course='"+"' OR course='".join(course)+"')"]
        if lang:
            conditions += ["(lang='"+"' OR lang='".join(lang)+"')"]
        if conditions:
            where += "WHERE " + " AND ".join(conditions)
        sql = select + where + groupby
        print(sql)
        result = cur.execute(sql).fetchall()
        results = []
        for row in result:
            a,b,c = row
            results.append([a,b,c])
        return results

    def process_promotion_stats(self,results):
        '''
        processes promotion stats generated by get_promotion_stats:
        Plots and outputs and csv string
        '''
        import matplotlib
        matplotlib.style.use('ggplot')
        df = pd.DataFrame(result,columns=["Rep","Cases","Values"])
        df.pivot(index='Cases', columns="Rep", values='Values')
        df2 = df.groupby(['Rep', 'Cases']).agg({'Values': 'sum'})
        dfper=df2.groupby(level=0).apply(lambda x: 100*x/float(x.sum())) #Calculate percentajes instead of absolute values
        dfper.unstack().transpose() #Transpose for easier visualization
        test=df.groupby(['Rep', 'Cases']).agg({'Values': 'sum'}).groupby(level=0).apply(lambda x: 100*x/float(x.sum())).unstack().transpose().fillna(0).sort(['F'],ascending=[0]).reset_index(1).reset_index(drop=True).set_index('Cases') #All in one
        print(test.to_csv())
        fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.25)
        test.plot(ax=ax,kind='bar')
        plt.title(",".join(course+year+lang))
        plt.show()

if __name__=="__main__":
    data = database("mendillorri.db")
    #data.insert_names(["data/izenak07-08.csv","data/izenak08-09.csv","data/izenak09-10.csv","data/izenak10-11.csv","data/izenak11-12.csv","data/izenak12-13.csv","data/izenak13-14.csv","data/izenak14-15.csv","data/izenak15-16.csv"])
    #data.insert_yeardata(["data/prom07-08.csv","data/prom08-09.csv","data/prom09-10.csv","data/prom10-11.csv","data/prom11-12.csv","data/prom12-13.csv","data/prom13-14.csv","data/prom14-15.csv"])
    #path = "/media/asier/ERREGESTOM/dptosn.csv"
    #data.insert_abreviatons(path)
    con = sqlite3.connect(data.db)
    cur = con.cursor()
    r=cur.execute("select distinct(course) from yeardata")
    c=[a[0] for a in r]
    for co in c:
        print(co)
        data.get_promotion_stats(course=[co])
    langs = [["D"],["A","G"]]
    for l in langs:
        print(l)
        for co in c:
            print(co)
            data.get_promotion_stats(course=[co],lang=l)

    course=["1. DBH"]
    year=["2007-2008","2008-2009","2009-2010","2010-2011","2011-2012","2012-2013","2013-2014","2014-2015"]
    lang=["D"]
    result = data.get_promotion_stats(course=course,year=year,lang=lang)
    data.process_promotion_stats(result)
    lang=["A","G"]
    result = data.get_promotion_stats(course=course,year=year,lang=lang)
    data.process_promotion_stats(result)
    lang=["A"]
    result = data.get_promotion_stats(course=course,year=year,lang=lang)
    data.process_promotion_stats(result)
    #Query to know how many of the sutdents that have repeated any course had gotten the ESO degree:
    #select promoting,count(promoting) from yeardata where course="4. DBH" AND uniquename IN (select distinct(uniquename) from yeardata where  yeardata.repeating="T") group by promoting
    #import database
    #data = database.database("mendillorri.db")
    #notak=["data/notak07-08.csv","data/notak08-09.csv","data/notak09-10.csv","data/notak10-11.csv","data/notak11-12.csv","data/notak12-13.csv","data/notak13-14.csv","data/notak14-15.csv","data/notak15-16.csv"]
    #data.insert_grades(notak)
    #Pendientes: select yeardata.course, yeardata.year, count(grades.subject) as pendientes,yeardata.uniquename,yeardata.promoting from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and not yeardata.course=grades.course and grades.period="1. Ebaluazioa" group by yeardata.uniquename,yeardata.year order by pendientes
    #All: select yeardata.course, yeardata.year, yeardata.uniquename,yeardata.promoting from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and  yeardata.course=grades.course and grades.period="1. Ebaluazioa" group by yeardata.uniquename,yeardata.year order by yeardata.uniquename luego hay que quitar de estos la combinación uniquename-course que ya tiene pendientes según la consulta anterior
    #Pendientes en 2. ESO: select yeardata.course, yeardata.year, count(grades.subject) as pendientes,yeardata.uniquename,yeardata.promoting from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and not yeardata.course=grades.course and grades.period="1. Ebaluazioa" and yeardata.course="2. DBH" group by yeardata.uniquename,yeardata.year order by pendientes
    '''Lo cuenta
    select re.pendientes,re.promoting,count(re.uniquename) from (select yeardata.course, yeardata.year, count(grades.subject) as pendientes,yeardata.uniquename,yeardata.promoting from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and not yeardata.course=grades.course and grades.period="1. Ebaluazioa" and yeardata.course="2. DBH" group by yeardata.uniquename,yeardata.year order by pendientes) as re group by re.pendientes,re.promoting
    '''
    #Buscar una consulta que saque los que no tienen pendientes
    '''
    SELECT    *
    FROM      yeardata
    LEFT JOIN (select yeardata.uniquename,yeardata.year,count(grades.subject) as pend from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and not yeardata.course=grades.course and grades.period="1. Ebaluazioa" and yeardata.course="2. DBH" group by yeardata.uniquename,yeardata.year) as pending
      ON pending.year=yeardata.year
      AND pending.uniquename=yeardata.uniquename
    where yeardata.course="2. DBH"
    AND (pending.year IS NULL
      OR pending.uniquename IS NULL);
    ''' #Estará bien?
    '''Lo mismo pero cuenta cuantos en cada tipo de promoción
      SELECT    promoting, count(yeardata.uniquename)
    FROM      yeardata
    LEFT JOIN (select yeardata.uniquename,yeardata.year,count(grades.subject) as pend from yeardata, grades where yeardata.uniquename=grades.uniquename and yeardata.year=grades.year and not yeardata.course=grades.course and grades.period="1. Ebaluazioa" and yeardata.course="2. DBH" group by yeardata.uniquename,yeardata.year) as pending
      ON pending.year=yeardata.year
      AND pending.uniquename=yeardata.uniquename
    where yeardata.course="2. DBH"
    AND (pending.year IS NULL
      OR pending.uniquename IS NULL)
    group by promoting
    '''