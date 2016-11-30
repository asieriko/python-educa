# -*- coding: utf-8 -*-
# from __future__ import division
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import csv
import os
from _collections import defaultdict


class notak:

    html = ""
    barcolors = ['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3']
    plt.rc('axes', facecolor='#FFFEEE', edgecolor='#4E3629')
    plt.rc('patch', facecolor='#6CA439', edgecolor='#517B2B', linewidth=0)
    plt.rc('figure', figsize=(16,6))
    plt.rc('font', size=14.0)
    plt.rc('axes', color_cycle=barcolors)
    plt.rc('lines', linewidth=4)

    def __init__(self, db, lang='es'):
        """
        Initiates the class
        :param db: the sqlite3 db file path
        :return: None
        """
        self.db = db
        self.periods = []
        self.workdir = ""
        self.excludedCourses = []
        self.year = ""
        self.langg = lang
        self.subjectsavg = defaultdict(defaultdict)

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
        self.year = year
        self.periods = periods
        #self.excludedCourses = [str(ec.decode()) for ec in excludedCourses]
        self.excludedCourses =  excludedCourses
        notcourses = "NOT results.course = '" + ("' AND NOT results.course = '").join(
            excludedCourses) + "'"  # The query works if excludedCourses = []
        notabreviations = "NOT abreviations.course = '" + (
        "' AND NOT  abreviations.course = '").join(
            baliogabekolaburdurak) + "'"  # The query works if baliogabekolaburdurak = []
        self.ebnumber = unekoeb
        if self.ebnumber > len(self.periods):
            print("Error: ebnumber > eb kopurua")

        ebselect = "results.period = '" + ("' OR results.period = '").join(
            self.periods[:self.ebnumber]) + "'"
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
        self.df['coursename'] = self.df.iloc[:, 2].map(self.coursecopy)
        self.df['coursenumber'] = self.df.iloc[:, 2].map(self.coursenumber)
        # iragazi beharko litzateke ere aurreko urteko pendienteak if coursenumber != subjcourse
        # df=df.rename(columns={'coursename':'course'})
        # df=df[df['subjcourse'] == df['subjcourse']]
        self.df = self.df.drop('course', axis=1)

    def generatepending(self):
        """
        Generates a pandas dataframe with pending subjects (the ones not passed from the previous course)
        :return:
        """
        self.dfp = self.df[self.df['subjcourse'] != self.df['coursenumber']]
        # some subjects can be coursed in 1-2 bach (IKT,MUSH,NGH) so they appear
        # as pending for those who course them in 2 bach
        self.dfp = self.dfp[self.dfp['abv_eu'] != 'IKT']
        self.dfp = self.dfp[self.dfp['abv_eu'] != 'MUSH']
        self.dfp = self.dfp[self.dfp['abv_eu'] != 'NGH']


    def removepending(self):
        """
        Removes pending subjects from the dataframe
        :return:
        """
        self.df = self.df[self.df['subjcourse'] == self.df['coursenumber']]

    def setWorkDir(self, wdir):
        # if wdir doesn't exists create it, else error:
        # No such file or directory, create also workdir+/pics
        self.workdir = wdir + "/"

    def createDir(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def generatetableDB(self):
        """
        Generates the database for storing the information
        :return:
        """
        con = sqlite3.connect(self.db)
        con.execute('''CREATE TABLE results
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            year           TEXT   NOT NULL,
            cgroup        TEXT NOT NULL,
            course        TEXT  NOT NULL,
            language        TEXT  NOT NULL,
            subject        TEXT  NOT NULL,
            period        TEXT  NOT NULL,
            student       TEXT NOT NULL,
            grade         INTEGER);''')
        print("Results table created successfully")
        con.execute('''CREATE TABLE abreviations
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            name           TEXT   NOT NULL,
            abv_es        TEXT NOT NULL,
            abv_eu        TEXT  NOT NULL,
            course        INT NOT NULL,
            dept           TEXT NOT NULL);''')
        print("Abreviations table created successfully")
        con.close()

    def insertdataDB(self, files):
        '''
        :param files: A list of csv files with the following format:
        Ikasturtea,Taldea,Kurtso,Hizkuntza eredua,Izen Osoa,Irakasgaiaren Izena,Ebaluaketa,Zenbakizko nota ohikoa
        ['2013-2014', '1. I', '1. DBH', 'D', 'XXXXX', 'Gizarte Zientziak, Geografia eta Historia BH1', '2. Ebaluaketa', '9']
        :return: None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='results'").fetchall()[0][
            0] == 0:
            self.generatetableDB(cur)
        for file in files:
            with open(file, 'r', encoding="ISO-8859-1") as results:
                reader = csv.reader(results)
                next(reader, None)  # skip first row with headers
                for row in reader:
                    print(row)
                    if row[7] != '':
                        grade = int(row[7])
                    else:
                        grade = ''
                    cur.execute(
                        "INSERT INTO results(year, cgroup, course, language, subject, period, student, grade) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                        (row[0], row[1], row[2], row[3], row[5], row[6], row[4], grade))
        con.commit()
        con.close()

    def insertabrDB(self, file):
        '''
        :param file: A file with the following format:
        Subject,LAB,ABR,course
        Arte eta Teknologia Esparrua 1,ATE,AAT,1
        :return None
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        print("Opened database successfully")
        # if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='results'").fetchall()[0][0] == 0:
        #    generatetableDB(cur)
        with open(file, 'r') as abrevs:
            reader = csv.reader(abrevs)
            next(reader, None)  # skip first row with headers
            for row in reader:
                cur.execute("INSERT INTO abreviations(name, abv_eu, abv_es, course, dept) VALUES(?, ?, ?, ?, ?)",
                            (row[0], row[1], row[2], row[3], row[4]))
        con.commit()
        con.close()

    def getsubjectsDB(self):
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

    def getyearsDB(self):
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

    def getcoursesDB(self, year=None, student=None):
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

    def percent(self, x, n=5):
        """
        Calculates the % of >=5 marks (from 10) in a list x
        :param x: list with grades (0-10)
        :return:
        """
        return sum(1 for a in x if a >= n) * 100 / len(x) if len(x) != 0 else ''

    def lowerThan(self,x,n=5):
        return sum(1 for a in x if a < n)


    def modelo(self, x):
        """
        :param x:list with course language
        :return:D for D and AG for A or G
        """
        if x == 'D':
            return 'D'
        else:
            return 'AG'

    # Same for ESO and Bach! Maybe is not important
    # Used for using only current courses subjects
    # but keep in mind
    def coursenumber(self, x):
        """
        :param x: Full Course Name: 2. DBH
        :return: Course Number: 2
        """
        return int(x[0])

    def coursecopy(self, x):
        return x

    def head(self):
        print(self.df.head())

    def generatesheet(self, group):
        """
        Generates a table for selected group, current year and period with the marks of each student and subject
        :param group: Name of the group
        :return: dataframe object with students as rows and subjects as columns
        """
        # Ebaluaketen bb egiten du! eta urteena ere egingo luke ikasle batek taldez errepikatuz bero, iragazi
        return self.generatesheet(group, self.year)

    def generatesheet(self, group):
        # Ebaluaketen bb egiten du! eta urteena ere egingo luke ikasle batek taldez errepikatuz bero, iragazi
        # Only for current year and eb'
        return pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.ebnumber - 1])], index=["student"], values=["grade"],
                              columns=["subject"]).fillna('')


    def notPassedStats(self,x):
        """
        From a list returns a dic with the number of not passed subjects and students
        :param x: dataframe with names and grades
        :return: a dic with the number of not passed subjects and students
        """
        gradescount = defaultdict(int)
        for y in x:
            gradescount[y] += 1
        return gradescount

    def prevnotpassedstats(self,x):
        allPassed = 0
        oneTwo = 0
        threeFour = 0
        more4 = 0
        for y in x:
            if y == 0: allPassed += 1
            if y in [1,2]: oneTwo += 1
            if y in [3,4]: threeFour += 1
            if y > 4: more4 += 1
        return [allPassed,oneTwo,threeFour,more4]

    def generateCoursePlots(self, func):
        """
        This funcition generates 3 plots for each course: One for AG languages, another for D and
        the last one for all of them for current year and period
        If the period is not the first, plots have a series with the previous period
        All plots have a series with the average of the last "5" years
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        for lang in ['AG', 'D', None]:  # [df.lang.unique(),None]:
            if lang:
                dflang = self.df[self.df['lang'] == lang]
            else:
                dflang = self.df
            for course in dflang[dflang.year == self.year].coursename.unique():
                if course in self.excludedCourses:
                    continue
                print(self.year, course)
                dfpivot = dflang[dflang['coursename'] == course]
                test = pd.pivot_table(dfpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"],
                                      aggfunc=func)
                selectperiods = test.swaplevel(0, 2, axis=1)
                selectyears = test.swaplevel(0, 1, axis=1)
                currenteb = selectperiods[self.periods[self.ebnumber - 1]]
                years = dfpivot.year.unique()
                years = years[-6:] if len(years) > 6 else years
                diagram = pd.DataFrame()
                diagram['cur'] = currenteb[currenteb.keys()[-1]]
                diagram['avg5y'] = currenteb[years[:-1]].mean(axis=1)
                if self.ebnumber != 1:
                    previouseb = selectperiods[self.periods[self.ebnumber - 2]]
                    diagram['prev'] = previouseb[previouseb.keys()[-1]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram['prev'].mean(), diagram['cur'].mean(), diagram['avg5y'].mean())],
                                     index=["AVG"], columns=['prev', 'cur', 'avg5y']))
                else:
                    diagram = diagram.append(
                        pd.DataFrame([(diagram['cur'].mean(), diagram['avg5y'].mean())], index=["AVG"],
                                     columns=['cur', 'avg5y']))
                if lang:
                    gtitle = course + '-' + lang
                else:
                    gtitle = course + '-All'
                # diagram.plot(kind='bar',title=gtitle).legend(loc='center left', bbox_to_anchor=(1,0.5))
                diagram.plot(kind='bar', title=gtitle).legend()
                # plt.show()
                if func.__name__ == 'mean':
                    plt.axhline(5)
                else:
                    plt.axhline(70)
                plt.savefig(self.workdir+"/"+gtitle + self.periods[self.ebnumber - 1] + '-' + func.__name__ + '-'+self.langg+'.png')
                plt.close()

    def generateGroupPlots(self, func):
        """
        This funcition generates 3 plots for each group: One for AG languages, another for D and
        the last one for all of them for current year and period
        If the period is not the first, plots have a series with the previous period
        All plots have a series with the average of the last "5" years
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            print(self.year, group)
            dfpivot = self.df[(self.df['cgroup'] == group) & (self.df['year'] == self.year)]
            test = pd.pivot_table(dfpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
            selectperiods = test.swaplevel(0, 2, axis=1)
            selectyears = test.swaplevel(0, 1, axis=1)
            currenteb = selectperiods[self.periods[self.ebnumber - 1]]
            diagram = pd.DataFrame()
            diagram['cur'] = currenteb[currenteb.keys()[-1]]
            if self.ebnumber != 1:
                previouseb = selectperiods[self.periods[self.ebnumber - 2]]
                diagram['prev'] = previouseb[previouseb.keys()[-1]]
                diagram = diagram.append(pd.DataFrame([(diagram['prev'].mean(), diagram['cur'].mean())], index=["AVG"],
                                                      columns=['prev', 'cur']))
            else:
                diagram = diagram.append(pd.DataFrame([(diagram['cur'].mean())], index=["AVG"], columns=['cur']))
            gtitle = group + "(" + self.year + ")" + self.periods[self.ebnumber - 1]
            # diagram.plot(kind='bar',title=gtitle).legend(loc='center left', bbox_to_anchor=(1,0.5))
            diagram.plot(kind='bar', title=gtitle).legend()
            # plt.show()
            if func.__name__ == 'mean':
                plt.axhline(5)
            else:
                plt.axhline(70)
            plt.savefig(self.workdir+"/"+gtitle + '-' + func.__name__ + '-'+self.langg+'.png')
            plt.close()

    def generateGroupStatsPlots(self):
        """
        This function generates a plot for each group: 0-2 not passed, 3-4 and 5 or more
        for current year and period
        :return:creates plots with 2 subplots, the first one an histogram with the number of students with X not passed
        subjects, and another pie diagrm with promotion information (0-2,3-4,>4)
        Also returns a dic with groups as keys and [number of not passed subjects, number of studengs with all passed,
        1-2 missed, 3-4 missed,>4 missed]
        """
        allg = defaultdict(str)
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            print(group)
            pt = pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
            self.df.period == self.periods[self.ebnumber - 1])], index=["student"], values=["grade"],
                              aggfunc=self.lowerThan).fillna('')
            missed = self.notPassedStats(pt.grade)
            if self.langg=="eu":
                 title = 'Ikasle vs ez gainditutakoak'
                 title2 = 'Promozioa'
            else:
                 title = 'Alumnos vs suspensos'
                 title2 = u'Promoción'
            p,prom,riesgo,peligro, left,legendhist,allg = self.generatePiedata(missed,allg,group)
            legendpie = ("<=2","3-4","=>5")
            colors = ['#6CA439', '#FF9C42', '#FF4848']
            plt.suptitle(group, fontsize=14)
            plt.subplot(1,2,1)
            plt.bar(left,prom,color='#6CA439')
            plt.bar(left,riesgo,color='#FF9C42')
            plt.bar(left,peligro,color='#FF4848')
            plt.title(title)
            plt.xticks(np.array(left)+0.5, legendhist)
            plt.subplot(1,2,2)
            plt.pie(p,labels=legendpie,colors=colors)
            plt.axis('equal')
            plt.title(title2)
            plt.savefig(self.workdir + "/" + group + "-" + self.periods[self.ebnumber-1] + "-" + self.langg + ".png")
            plt.close()
        return allg

    def generatePiedata(self,missed,allg,coursegroup,lang=''):
        mmissed = np.max([int(k) for k in missed.keys()])
        print(mmissed)
        if mmissed < 5: mmissed = 5
        prom=list([missed[0],missed[1],missed[2]])
        for k in range(3,mmissed+1):
            prom.append(0)
        riesgo = [0,0,0,missed[3],missed[4]]
        for k in range(5,mmissed+1):
            riesgo.append(0)
        peligro=list()
        for k in range(5):
            peligro.append(0)
        for k in range(5,mmissed+1):
            peligro.append(missed[k])
        value = 0.5
        left = []
        for k in range(0,mmissed+1):
            left.append(value)
            value += 1
        p = [0,0,0]
        t = 0
        for i in missed.keys():
            t += i*missed[i] #nº total de suspensos
            if i < 3: p[0] += missed[i]
            if i in [3,4]: p[1] += missed[i]
            if i > 4: p[2] += missed[i]
        allg[coursegroup+lang] = [t]+[prom[0]]+[p[0]-prom[0]]+p[1:]
        legendhist =  [str(i) for i in range(0,mmissed+1)]
        return p, prom, riesgo, peligro, left, legendhist, allg

    def generateAllStatsPlots(self,year=None,period=None):
        lang = 'eu'
        if not year: year = self.year
        if not period: period = self.periods[self.ebnumber - 1]
        pt = pd.pivot_table(self.df[(self.df.year == year) & (self.df.period == period)], index=["student"], values=["grade"], aggfunc=self.lowerThan).fillna('')
        missed = self.notPassedStats(pt.grade)
        p,prom,riesgo,peligro, left,legendhist,allg = self.generatePiedata(missed,{},'all',lang)
        print(self.generatePiedata(missed,allg,"all",lang))


    def generateCourseStatsPlots(self):
        """
        This funcition generates a plot for each course: 0-2 not passed, 3-4 and 5 or more
        for current year and period
        :return:creates plots with 2 subplots, the first one an histogram with the number of students with X not passed
        subjects, and another pie diagrm with promotion information (0-2,3-4,>4)
        Also returns a dic with courses as keys and [number of not passed subjects, number of studengs with all passed,
        1-2 missed, 3-4 missed,>4 missed]
        """
        #FIXME: Not only me, but save all pictures in a separate folder!
        allg = defaultdict(str)
        for lang in ['AG', 'D', None]:  # [df.lang.unique(),None]:
            if lang:
                dflang = self.df[self.df['lang'] == lang]
            else:
                dflang = self.df
            for course in dflang[dflang.year == self.year].coursename.unique():
                if not lang: lang = "All"
                print(course,lang)
                pt = pd.pivot_table(dflang[(dflang.coursename == course) & (dflang.year == self.year) & (
                dflang.period == self.periods[self.ebnumber - 1])], index=["student"], values=["grade"],
                                  aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                if self.langg=="eu":
                     title = 'Ikasle vs ez gainditutakoak'
                     title2 = 'Promozioa'
                else:
                     title = 'Alumnos vs suspensos'
                     title2 = u'Promoción'
                p,prom,riesgo,peligro, left,legendhist,allg = self.generatePiedata(missed,allg,course,lang)
                legendpie = ("<=2","3-4","=>5")
                colors = ['#6CA439', '#FF9C42', '#FF4848']
                plt.suptitle(course, fontsize=14)
                plt.subplot(1,2,1)
                plt.bar(left,prom,color='#6CA439')
                plt.bar(left,riesgo,color='#FF9C42')
                plt.bar(left,peligro,color='#FF4848')
                plt.title(title)
                plt.xticks(np.array(left)+0.5, legendhist)
                plt.subplot(1,2,2)
                plt.pie(p,labels=legendpie,colors=colors)
                plt.axis('equal')
                plt.title(title2)
                plt.savefig(self.workdir + "/" + course + "-" + lang + "-" + self.periods[self.ebnumber-1] + "-" + self.langg + ".png")
                plt.close()
        return allg


    def generatePassPercent(self,period,year,group = None):
        if group:
            framefilter = (self.df['period']==period) & (self.df['year']==year) & (self.df['cgroup']==group)
        else:
            framefilter = (self.df['period']==period) & (self.df['year']==year)
        eh = pd.pivot_table(self.df[framefilter], index=["subject"], values=["grade"],margins=True,aggfunc=self.percent).fillna('')
        eh.columns = ["positivepercentage"]
        bad = eh[eh.positivepercentage<70]
        perbad = len(bad)*100/len(eh)
        print(period," of ",year," Course",str(group))
        print("Subject with less than %70 ap: %",perbad)
        print(bad)
        eh.to_csv("ehunekoak-"+period+"-"+year+"-"+str(group)+".csv")


    def generateORpandas(self,name, data):
        g = "( "
        for d in data:
            g = g + "(" + name + " == '" + d + "')"
            if len(data) > 1:
                g = g + " | "
        if len(data) > 1:  # Remove the last OR (agian with " OR ".join
            g = g[:-2]
        g = g + ")"
        return g

    def bardiagram(self,name, fname, data, legend):
        '''
        Input: [['Atzerriko Hizkuntza I: Ingelesa', '5', '4'], ['Hezkuntza Arreta', '7', '5'], ['Mundu garaikiderako zienztziak', '6', '6'], ['Gaztelania eta Literatura I', '4', '4'], ['Filosofia eta herritartarsuna', '1', '6'], ['Gorputz Hezkuntza', '9', '9'], ['Fisika eta Kimika', '5', '2'], ['Teknologia industriala I', '5', '4'], ['Matematika I', '2', '2'], ['Marrazketa Teknikoa I', '3', '2'], ['BB', '4.7', '4.4']]
        Output: A bar diagram with X subjects, and columns for each evaluation period, and the average grade
        '''
        plt.clf()
        l = len(data[0])
        colors = ['#6CA439','#FF9C42','#FF4848','#3074AE']
        ind = np.arange(len(data))    # the x locations for the groups
        width = 0.3       # the width of the bars: can also be len(x) sequence
        for i in range(l - 1):
            plt.bar(ind + i * width, [float(b[i + 1]) for b in data], width,
            color=colors[i], label=legend[i])
        #plt.bar(ind+2*width, eb2, width, color='y',label='2. Ebaluaketa')
        plt.ylabel('Notak')
        plt.title(name + '\nKurtsoaren garapena')
        plt.xticks(ind + (l - 1) * width / 2, [b[0] for b in data], rotation=90)
        plt.yticks(np.arange(0, 11, 1))
        plt.subplots_adjust(bottom=0.20)
        plt.legend()
        plt.savefig(fname, format="png")

    def generateStatsSubjectsPandas(self):
        pts = pd.pivot_table(self.df[self.df.year == self.year], rows=["coursename","subject"],values=["grade"],cols=["lang","period"],margins=True,aggfunc=np.mean).fillna('')
            #pts.ix['1. Batxilergoa LOE'].ix["Latina I"][0] AG 1. eb (bakarrik 1 eb)
            # n.subjectsavg["2015-2016"].ix['2. Batxilergoa LOE'].ix["Latina II"].grade.AG[0] 1. eb
        self.subjectsavg[year] = pts

    def generateStatsStudentPandas(self,year,ebal):
        students = self.df[self.df.year == self.year].student.unique()#FIXME excludedCourses?
        print("<html><body>")
        for student in students:
            print("<h1>",student,"</h1>")
            pts = pd.pivot_table(self.df[(self.df.student == student) & (self.df.year == self.year)], rows=["subject"],values=["grade"],cols=["period"],margins=True,aggfunc=np.mean).fillna('')
            print(pts.to_html())
        print("</body></html>")
            

    # Pendienteak kurtsoan bertan agertzen dira, 2. batx badu 1. batx pendiente course=2. batx
    def generateStatsStudent(self, year, ebal, mod=None, groups=None):
        '''
        Generates a html file foreach group, which includes a table with each student marks (present and past periods)
        and also a graph with the same data plus a column with the average of the course
        '''
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        ebals = self.periods[:self.periods.index(ebal) + 1]
        legend = [e for e in ebals]
        legend.append("mailaren BB")
        groupsp = groups
        if not groups:
            courses = self.df[self.df.year == self.year].coursename.unique()#FIXME excludedCourses?
        else:
            #g = generateOR("cgroup", groups)
            #courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=? AND period=? AND " + g, [year, ebals[-1]]).fetchall() if c[0].encode("utf8") not in self.excludedCourses]
            g1 = self.generateORpandas("self.df.cgroup", groups)
            filter = "(self.df.year == self.year) & (self.df.period == ebal ) & " + g1
            courses = self.df[eval(filter)].coursename.unique()
        for course in sorted(courses):
            print(course)
            subjectsavg = {}
            subjects = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].subject.unique()
            avgpandas = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
            avgpandasA = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["coursename"],values=["grade"],margins=True,aggfunc=np.mean).fillna(0)
            badsubjectscoursept = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')
            badsubjectscourse = badsubjectscoursept[badsubjectscoursept.grade<70]
            for subject in subjects:
                subjectsavg[subject] = str(avgpandas.ix[subject].grade)
            avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchone()#FIXME to pandas
            subjectsavg["BB"] = str(avg[0])
            print("AVG: ",avgpandas,avgpandasA,subjectsavg)
            # Use a function wich generates stats for the course
            groups = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].cgroup.unique()
            if groupsp:
                groups = [g for g in groups if g in groupsp]
            for group in groups:
                #self.generateGroupStatsGradeAverage(year, ebals, course, [(group)]) #Generates the average grade for each subject
                students = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.cgroup == group)].student.unique()
                groupgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.cgroup == group)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
                print(group)
                # Use a function wich generates stats for the group
                htmlmenu = ""
                ghtml = ""
                for student in sorted(students):
                    print(student)
                    htmlmenu = htmlmenu + '<li><a href=\"#' + "-".join(str(student).split()) + '\">' + student + '</a></li>'
                    '''
                    #subjects = [s[0] for s in cur.execute("SELECT DISTINCT subject FROM results WHERE year=? AND period=? AND course=? AND student=?", [year, ebals[-1], course, student]).fetchall()]
                    subjects = [s[0] for s in cur.execute("SELECT DISTINCT results.subject FROM results,abreviations WHERE results.year = ? AND results.period=? AND results.course=? AND results.student=? AND results.subject=abreviations.name AND abreviations.course=?", [year, ebals[-1], course, student,course[0]]).fetchall()] #FIXME to pandas
                    subjects.sort()
                    summary = []
                    for subject in subjects:
                        subsum = []
                        #print(subject)
                        subsum.append(subject)
                        for period in ebals:
                            grades = cur.execute("SELECT grade FROM results WHERE year=? AND period=? AND course=? AND student=? AND subject=?", [year, period, course, student, subject]).fetchone()#FIXME to pandas
                            #print(period,grades)
                            if grades:
                            # Assume 0 if not graded or grade None (coming from other school)
                                if grades[0] == '':
                                    subsum.append(str(0))
                                else:
                                    subsum.append(str(grades[0]))
                            else:
                                subsum.append(str(0))
                        subsum.append(subjectsavg[subject])
                        if (not [True in [a == '' for a in subsum[1:]]][0]):
                        # Some students doesn't have all the subjects #FIXME strange code, maybe -> 0
                            summary.append(subsum)
                            '''
                    studentgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.student == student)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
                    print(studentgrades.info())
                    print(studentgrades)
                    studentgrades = studentgrades.reset_index().merge(groupgrades, how="left").set_index('subject')
                    print(studentgrades)
                    '''
                    subsum = []
                    subsum.append("BB")
                    for period in ebals:
                        avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=? AND student=?", [year, period, course, student]).fetchone()#FIXME to pandas
                        if avg[0]:
                            subsum.append(str(avg[0]))
                        else:
                            subsum.append(str(0))
                    subsum.append(subjectsavg["BB"])
                    summary.append(subsum)
                    print("Student: ",summary,studentgrades)
                    '''
                    fname = year + "-" + ebal + "-" + student + ".png"
                    '''
                    if summary != []:
                        cur = con.cursor()
                        for s in summary[:-1]:
                            n = cur.execute("select abv_eu from abreviations where name=?", [s[0]]).fetchone()[0]
                            s[0] = n
                        self.createDir(self.workdir + group)
                        #self.bardiagram(student, self.workdir + group +"/" + fname, summary, legend)
                    '''
                    html = ""
                    html = html + '''
                    <div class="student">
                        <h1 style=\"clear: both;\" id='%s'></h1>
                        <h1> %s  <a href=#top>(top)</a></h1>
                        <div class="row" style=\"display: flex; align-items: center;\">
                        <div class="col-md-3 col-sm-6">'''%("-".join(str(student).split()),student)
                        #<table class=\"table table-striped\" border="1" text-aling="center">
                            #<tr>
                                #<th>Ikasgaia</th>'''%("-".join(str(student).split()),student)
                    #for e in ebals:
                        #html = html + "<th>" + e + "</th>\n"
                    #html = html + "</tr>\n"
                    #print(summary)
                    #for s in summary:
                        #if len(summary)>2 and float(s[-2])<float(s[-1]):
                            #html = html + "<tr class=\"danger\">"
                        #elif float(s[-2])>float(s[-1]):
                            #html = html + "<tr class=\"success\">"
                        #else:
                            #html = html + "<tr>"
                        #for a in s[:-1]:
                            #html = html + "<td>" + a + "</td>\n"
                        #html = html + "</tr>\n"
                    #html = html + '''</table>
                    html = html + studentgrades.to_html(classes="table table-striped") + '''</div>
                    <div class="col-md-7 col-sm-6">
                    <img class="img-responsive center-block"  style=\"float: left; margin: 0px 0px 15px 15px;vertical-align: middle;\" src=\"%s/%s\">
                    </div>
                    </div>
                    </div>'''%(group,fname)
                    ghtml = ghtml + html
                #self.generateGroupStatsPlots()#year, ebal, group=group)
                #pie = str(group) + "/" + year + "-" + ebal + str(group) + ".png"
                pie = str(group) + "-" + ebal + "-" + self.langg + ".png"
                mean = str(group) + "(" + self.year +")" + ebal + "-mean-" + self.langg + ".png"
                percent = str(group) + "(" + self.year +")" + ebal + "-percent-" + self.langg + ".png"
                badsubjectsgrouppt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.cgroup == group)],rows=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')
                badsubjectsgroup = badsubjectsgrouppt[badsubjectsgrouppt.grade<70]
                ghtml = '''
                <!DOCTYPE html>
                <html lang="eu">
                    <head>
                        <meta charset=\"utf-8\">
                        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css">
                        <link href="dashboard.css" rel="stylesheet">
                    </head>
                    <body>
                        <nav class="navbar navbar-inverse navbar-fixed-top">
                          <div class="container-fluid">
                            <div class="navbar-header">
                              <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
                                <span class="sr-only">Toggle navigation</span>
                                <span class="icon-bar"></span>
                                <span class="icon-bar"></span>
                                <span class="icon-bar"></span>
                              </button>
                              <a class="navbar-brand" href="#">Ikasleen emaitzak</a>
                            </div>
                          </div>
                        </nav>
                    <div class=\"container-fluid\">
                        <div style="margin-top: 2cm;" class=\"row\">
                            <div class=\"col-sm-2 col-md-2 sidebar\">
                                <ul class=\"nav nav-sidebar\">
                                %s
                                </ul>
                            </div>
                            <div class=\"col-sm-8 col-sm-offset-2 col-md-8 col-md-offset-2 main\">
                                <h1 class=\"page-header\" id=top>Taldeko emaitzak</h1>
                                <h2 class=\"page-header\" id=top>Promozioa</h2>
                                <img class="img-responsive center-block" src=\"%s\">
                                <h2 class=\"page-header\" id=top>Batazbestekoa</h2>
                                <img class="img-responsive center-block" src=\"%s\">
                                <h2 class=\"page-header\" id=top>Gaindituen ehunekoak</h2>
                                <img class="img-responsive center-block" src=\"%s\">
                                <h2>ehuneko 70 baino gainditu gutxiago duten ikasgaiak</h2>
                                %s
                                <h1 class=\"page-header\">Ikasleen emaitzak</h1>
                                %s
                            </div>
                        </div>
                    </div>
                    <!-- Bootstrap core JavaScript
                    ================================================== -->
                    <!-- Placed at the end of the document so the pages load faster -->
                    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>
                    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js">
                    <script src="../../assets/js/docs.min.js"></script>
                    </body>
                </html>
                '''%(htmlmenu,pie,mean,percent,badsubjectscourse.to_html(classes="table table-striped"),ghtml)
                f = open(self.workdir + group + ".html", 'w')
                f.write(ghtml) #  f.write(ghtml.encode("utf8"))
                f.close()

if __name__ == "__main__":
    db = "/home/asier/Hezkuntza/SGCC/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluacion/Python-educa/test2.db"
    ebaluaketak = ['1. Ebaluaketa', '2. Ebaluaketa', '3. Ebaluaketa', 'Azken Ebaluaketa', 'Ohiz kanpoko Ebaluaketa']
    baliogabekokurtsoak = [b'Programa de Curr\xc3\xadculo Adaptado']
    baliogabekokurtsoak = ['Programa de Currículo Adaptado']
    baliogabekolaburdurak = []
    files = ["/home/asier/Hezkuntza/SGCC-Erregistroak-15-16/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluación/1º Ev/Sabanas 2º Bach 27-11/1ev-2bach.csv"]
    year = "2015-2016"
    n = notak(db,'es')
    n.setWorkDir("ezabatu/")
    #n.insertdataDB(files)
    n.configure(year, ebaluaketak, 1, baliogabekokurtsoak, baliogabekolaburdurak)
    n.removepending()
    #a = n.generateStatsSubjectsPandas("2015-2016","1. Ebaluaketa")
    #n.generateStatsStudentPandas("2015-2016", "1. Ebaluaketa")
    n.generateStatsStudent("2015-2016", "1. Ebaluaketa",groups=("Bach.2A","Bach.2B","Batx.2H","Batx.2I","Batx.2J"))
    n.generateAllStatsPlots()
    #n.generatePassPercent("Azken Ebaluaketa","2014-2015")
    #n.generatePassPercent("Azken Ebaluaketa","2013-2014")
    taldeak = n.df[n.df.year == "2015-2016"].cgroup.unique()
    for t in taldeak:
        n.generatePassPercent("1. Ebaluaketa","2015-2016",t)

    ag = n.generateGroupStatsPlots()
    ac = n.generateCourseStatsPlots()
    n.generateCoursePlots(n.percent)
    n.generateGroupPlots(n.percent)
    #m = notak(db)
    #m.configure(year, ebaluaketak, 1, baliogabekokurtsoak, baliogabekolaburdurak)
    n.generateCoursePlots(np.mean)
    n.generateGroupPlots(np.mean)