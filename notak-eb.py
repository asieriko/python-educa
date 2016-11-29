# -*- coding: utf-8 -*-
# from __future__ import division
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import csv
import os
from _collections import defaultdict
from matplotlib import rcParams
#rcParams.update({'figure.autolayout': True}) #TODO it makes small plogs with very big labels, I've to figure how to change subject names with abreviations


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
        self.studpasstitle = {'eu': 'Ikasle vs ez gainditutakoak','es':'Alumnos vs suspensos'}
        self.promttitle = {'eu':'Promozioa','es':u'Promoción'}
        self.cur= {'eu':'Oraingoa','es':'Actual'}
        self.prev= {'eu':'Aurrekoa','es':'Anterior'}
        self.avg= {'eu':'BB','es':'Prom'}
        self.avg5 = {'eu':'BB5u','es':'Prom5a'}
        self.langt = {'eu':'Eredu-maila','es':'Modelo-nivel'}

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
            with open(file, 'r', encoding="UTF-8") as results:
                reader = csv.reader(results)
                next(reader, None)  # skip first row with headers
                for row in reader:
                    print(row)
                    if row[10] != '':
                        grade = int(row[10])
                    else:
                        grade = ''
                    cur.execute(
                        "INSERT INTO results(year, cgroup, course, language, subject, period, student, grade) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                        (row[0], row[1], row[2], row[3], row[7], row[9], row[4], grade))
                    #FIXME:Ikasturtea,Taldea,Kurtso,Hizkuntza eredua,Izen Osoa,Usuario EDUCA,Erabiltzaile izen bakarra,Irakasgaiaren Izena, Irakasgaiaren Kurtsoa,Ebaluaketa,Zenbakizko nota ohikoa

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
        #FIXME: Dirty hack
        if x[0] not in ['p','P']:
            return int(x[0])
        else:
            return 0
        

    def coursecopy(self, x):
        return x

    def head(self):
        print(self.df.head())


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
                diagram[self.cur[self.langg]] = currenteb[currenteb.keys()[-1]]
                diagram[self.avg5[self.langg]] = currenteb[years[:-1]].mean(axis=1)
                if self.ebnumber != 1:
                    previouseb = selectperiods[self.periods[self.ebnumber - 2]]
                    diagram[self.prev[self.langg]] = previouseb[previouseb.keys()[-1]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[self.prev[self.langg]].mean(), diagram[self.cur[self.langg]].mean(), diagram[self.avg5[self.langg]].mean())],
                                     index=[self.avg[self.langg]], columns=[self.prev[self.langg], self.cur[self.langg], self.avg5[self.langg]]))
                else:
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[self.cur[self.langg]].mean(), diagram[self.avg5[self.langg]].mean())], index=[self.avg[self.langg]],
                                     columns=[self.cur[self.langg], self.avg5[self.langg]]))
                if lang:
                    gtitle = course + '-' + lang
                else:
                    gtitle = course + '-All'
                # diagram.plot(kind='bar',title=gtitle).legend(loc='center left', bbox_to_anchor=(1,0.5))
                diagram.plot(kind='bar', title=gtitle).legend(loc=4)
                # plt.show()
                if func.__name__ == 'mean':
                    plt.ylim(0, 10)
                    plt.axhline(5)
                else:
                    plt.ylim(0, 100)
                    plt.axhline(70)
                plt.savefig(self.workdir+"/"+gtitle + self.periods[self.ebnumber - 1] + '-' + func.__name__ + '-'+self.langg+'.png')
                plt.close()


    def generateGroupPlots(self, group, func):
        """
        This function generates a plot for the group with the grades/pass% of each subject depending on func
        If the period is not the first, plots have a series with the previous period
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        print(self.year, group)
        lang = self.df[(self.df.year == year) & (self.df.cgroup == group)].lang.unique()[0]
        course = self.df[(self.df.year == year) & (self.df.cgroup == group)].coursename.unique()[0]
        print("Eredua: ",lang)
        langpivot = self.df[(self.df['lang'] == lang) & (self.df['year'] == self.year) & (self.df['coursename'] == course)]
        langpivot = pd.pivot_table(langpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        langperiods = langpivot.swaplevel(0, 2, axis=1)
        langyears = langpivot.swaplevel(0, 1, axis=1)
        langcurrent= langperiods[self.periods[self.ebnumber - 1]]
        dfpivot = self.df[(self.df['cgroup'] == group) & (self.df['year'] == self.year)]
        test = pd.pivot_table(dfpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        selectperiods = test.swaplevel(0, 2, axis=1)
        selectyears = test.swaplevel(0, 1, axis=1)
        currenteb = selectperiods[self.periods[self.ebnumber - 1]]
        currenttext =  "(" + group + ")" + self.cur[self.langg]
        prevtext = "(" + group + ")" + self.prev[self.langg]
        levellangtext = course + "(" + lang + ")"
        diagram = pd.DataFrame()
        diagram[levellangtext] = langcurrent[currenteb.keys()[-1]]
        diagram[currenttext] = currenteb[currenteb.keys()[-1]]
        if self.ebnumber != 1:
            previouseb = selectperiods[self.periods[self.ebnumber - 2]]
            diagram[prevtext] = previouseb[previouseb.keys()[-1]]
            diagram = diagram.append(pd.DataFrame([(diagram[levellangtext].mean(), diagram[prevtext].mean(), diagram[currenttext].mean())], index=[self.avg[self.langg]], columns=[levellangtext, prevtext, currenttext]))
        else:
            diagram = diagram.append(pd.DataFrame([(diagram[levellangtext].mean(), diagram[currenttext].mean())], index=[self.avg[self.langg]], columns=[levellangtext,currenttext]))
        gtitle = group + "(" + self.year + ")" + self.periods[self.ebnumber - 1]
        # diagram.plot(kind='bar',title=gtitle).legend(loc='center left', bbox_to_anchor=(1,0.5))
        diagram.plot(kind='bar', title=gtitle).legend(loc=4)
        # plt.show()
        if func.__name__ == 'mean':
            plt.ylim(0, 10)
            plt.axhline(5)
        else:
            plt.ylim(0, 100)
            plt.axhline(70)
        plt.savefig(self.workdir+"/"+gtitle + '-' + func.__name__ + '-'+self.langg+'.png')
        plt.close()

    def generateAllGroupPlots(self, func):
        """
        This function generates a plot for each group with the grades/pass% of each subject depending on func
        If the period is not the first, plots have a series with the previous period
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            print(self.year, group)
            self.generateGroupPlots(group,func)

    def generateGroupStatsPlots(self,group):
        pt = pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.ebnumber - 1])], index=["student"], values=["grade"],
                            aggfunc=self.lowerThan).fillna('')
        print(pt)
        missed = self.notPassedStats(pt.grade)
        title = self.studpasstitle[self.langg]
        title2 = self.promttitle[self.langg]
        p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed,group)
        print(group+";"+str(sum(prom))+";"+str(sum(peligro)))
        t = sum(p)
        p = [x *100/ t for x in p]
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
        plt.pie(p,labels=legendpie,autopct='%1.1f%%',colors=colors)
        plt.axis('equal')
        plt.title(title2)
        plt.savefig(self.workdir + "/" + group + "-" + self.periods[self.ebnumber-1] + "-" + self.langg + ".png")
        plt.close()
        

    def generateAllGroupStatsPlots(self):
        """
        This function generates a plot for each group: 0-2 not passed, 3-4 and 5 or more
        for current year and period
        :return:creates plots with 2 subplots, the first one an histogram with the number of students with X not passed
        subjects, and another pie diagrm with promotion information (0-2,3-4,>4)
        Also returns a dic with groups as keys and [number of not passed subjects, number of studengs with all passed,
        1-2 missed, 3-4 missed,>4 missed]
        """
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            #print(group)
            self.generateGroupStatsPlots(group)
            

    def generatePiedata(self,missed,coursegroup,lang=''):
        mmissed = np.max([int(k) for k in missed.keys()])
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
        legendhist =  [str(i) for i in range(0,mmissed+1)]
        return p, prom, riesgo, peligro, left, legendhist

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
                title = self.studpasstitle[self.langg]
                title2 = self.promttitle[self.langg]
                p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed,course,lang)
                t = sum(p)
                p = [x *100/ t for x in p]
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
                plt.pie(p,labels=legendpie,autopct='%1.1f%%',colors=colors)
                plt.axis('equal')
                plt.title(title2)
                plt.savefig(self.workdir + "/" + course + "-" + lang + "-" + self.periods[self.ebnumber-1] + "-" + self.langg + ".png")
                plt.close()
        return allg


    def generateYearsAllGoodSubjects(self,period,percentaje,years=None):
        years=['2007-2008','2008-2009','2009-2010','2010-2011','2011-2012','2012-2013','2013-2014','2014-2015','2015-2016']#FIXME: Not hardcoded
        good = []
        for year in years:
            eh = pd.pivot_table(self.df[(self.df['period']=="1. Ebaluaketa") & (self.df['year']==year)], index=["subject"], values=["grade"],margins=True,aggfunc=n.percent).fillna('')
            eh.columns = ["positivepercentage"]
            bad = eh[eh.positivepercentage<percentaje]
            pergood = 100-len(bad)*100/len(eh)
            good.append(pergood)
        return list(zip(years,good))

    def generatePassPercent(self,period,year,group = None,percentaje = 70):
        if group:
            framefilter = (self.df['period']==period) & (self.df['year']==year) & (self.df['cgroup']==group)
        else:
            framefilter = (self.df['period']==period) & (self.df['year']==year)
        eh = pd.pivot_table(self.df[framefilter], index=["subject"], values=["grade"],margins=True,aggfunc=self.percent).fillna('')
        eh.columns = ["positivepercentage"]
        bad = eh[eh.positivepercentage<percentaje]
        perbad = len(bad)*100/len(eh)
        print(period," of ",year," Course",str(group))
        print("Subject with less than %" + str(percentaje) + " ap: %",str(perbad))
        print(bad)
        #print("Group;" + str(group) +";"+ str(percentaje) + " ap: %;",str(100-perbad))
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
            print(pts.to_html(classes="table table-striped",float_format=lambda x: '%10.2f' % x))
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
            self.generateStatsCourse(year,ebals,course,mod)
            groups = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].cgroup.unique()
            if groupsp:
                groups = [g for g in groups if g in groupsp]
            for group in groups:
                print(group)
                subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent = self.generateStatsGroup(year, ebal, ebals, group)
                #self.generateGroupStatsGradeAverage(year, ebals, course, [(group)]) #Generates the average grade for each subject
                students = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.cgroup == group)].student.unique()
                htmlmenu = ""
                ghtml = ""
                for student in sorted(students):
                    print(student)
                    htmlmenu = htmlmenu + '<li><a href=\"#' + "-".join(str(student).split()) + '\">' + student + '</a></li>'
                    html = self.generateStatsStudent2(year,ebal,student,groupgrades)
                    ghtml = ghtml + html
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
                                <h2>Ikasleen suspentso kopurua eta notaren Batazbestekoa</h2>
                                %s
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
                '''%(htmlmenu,pie,studentsnotpasses.to_html(index=False,classes="table table-striped"),mean,percent,badsubjectsgroup.to_html(index=False,classes="table table-striped",float_format=lambda x: '%10.2f' % x),ghtml)
                f = open(self.workdir + group + ".html", 'w')
                f.write(ghtml) #  f.write(ghtml.encode("utf8"))
                f.close()

    def generateStatsCourse(self, year, ebals, mod=None, course=None):
        print(course)
        coursegrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        courseaverage = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["coursename"],values=["grade"],margins=True,aggfunc=np.mean).fillna(0)
        subjectscoursept = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],rows=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')
        badsubjectscourse = subjectscoursept[subjectscoursept.grade<70]
        badsubjectscourse.unstack()
        badsubjectscourse.reset_index(level=0,inplace=True)
        #Another way to calculate each course's subjects average
        #The average of all course is different with pandas or sql, does pandas calculate the avg of the avgs of each subject?
        subjectsavg = {}
        subjects = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].subject.unique()
        for subject in subjects:
            subjectsavg[subject] = str(coursegrades.ix[subject].grade)
        avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchone()#FIXME to pandas
        subjectsavg["BB"] = str(avg[0])
        print("AVG: ",subjectscoursept,badsubjectscourse,coursegrades,courseaverage,subjectsavg)

    def generateStatsGroup(self, year, ebal, ebals, group, diagrams=True):
        '''
        #FIXME: ebal and ebals!!
        for a year, period (ebals[-1], ebals should be alist), ebal is only used for titles. and a group
        generates:
        0- A list with all subjects passed %
        1- A list with subjects with less than 70 of students passess, and its %
        2- Average grade for each subject
        3- Number of not passed subjects, and average grade for each student
        4- Name for the pie plot
        5- Name for subjects mean plot
        6- Name for subjects percentaje plot
        Optionally if diagrms=True also generates those plots
        '''
        print(group)
        lang = self.df[(self.df.year == year) & (self.df.cgroup == group)].lang.unique()[0]
        print("Eredua: ",lang)
        #self.generateGroupStatsGradeAverage(year, ebals, course, [(group)]) #Generates the average grade for each subject
        students = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.cgroup == group)].student.unique()
        groupgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        groupgrades.unstack()
        groupgrades.reset_index(level=0, inplace=True)
        subjectsgrouppt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],rows=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')#this one could return percentajes of all subjects, not only bad ones!
        badsubjectsgroup = subjectsgrouppt[subjectsgrouppt.grade<70] #FIXME: 70 hardcoded
        badsubjectsgroup.unstack()
        badsubjectsgroup.reset_index(level=0,inplace=True)
        badsubjectsgroup.columns=["subject","%"]
        studentsnotpasses = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],index=["student"],values=["grade"],aggfunc=[self.lowerThan,np.mean]).fillna('')
        studentsnotpasses.unstack()
        studentsnotpasses.reset_index(level=0,inplace=True)
        studentsnotpasses.columns=["student","<5","avg"]
        studentsnotpasses.sort(['<5'],ascending=[0])      
        #self.generateGroupStatsPlots()#year, ebal, group=group)
        #pie = str(group) + "/" + year + "-" + ebal + str(group) + ".png"
        pie = str(group) + "-" + ebal + "-" + self.langg + ".png"
        mean = str(group) + "(" + self.year +")" + ebal + "-mean-" + self.langg + ".png"
        percent = str(group) + "(" + self.year +")" + ebal + "-percent-" + self.langg + ".png"
        if diagrams:
            self.generateGroupPlots(group, np.mean) #For all plots, pass year and ebal. Or should they be global? optional argument..
            self.generateGroupPlots(group, n.percent)
            self.generateGroupStatsPlots(group)
        return subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent

    def generateStatsStudent2(self,year,ebal,student,groupgrades):
        '''
        generates html with a table for the students with subjects and his marks side by side with all group marks
        studentgroupgrades is a DataFrame with those marks
        '''
        print(student)
        studentgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.student == student)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        studentgrades.unstack()
        studentgrades.reset_index(level=0, inplace=True)
        studentgroupgrades = pd.merge(studentgrades,groupgrades,on="subject")
        studentgroupgrades.columns = ['subject', 'student','course']
        print(studentgroupgrades)
        group=self.df[(self.df.student==student)&(n.df.year==year)].cgroup.unique()[0]#FIXME: I don't like looking up the group this way, but I don't like to pass to much paramters either
        self.createDir(self.workdir + group)
        fname = group + "/" + year + "-" + ebal + "-" + student + ".png" #to use self.workdir + group + "/" + we need to create group dir first self.createDir(self.workdir + group)
        plt.clf()
        studentgroupgrades.plot(kind="bar",x=studentgroupgrades.subject)
        plt.savefig(self.workdir + fname, format="png")
        html = ""
        html = html + '''
        <div class="student">
            <h1 style=\"clear: both;\" id='%s'></h1>
            <h1> %s  <a href=#top>(top)</a></h1>
            <div class="row" style=\"display: flex; align-items: center;\">
            <div class="col-md-3 col-sm-6">'''%("-".join(str(student).split()),student)
        html = html + studentgrades.to_html(index=False,classes="table table-striped",float_format=lambda x: '%10.2f' % x) + '''</div>
        <div class="col-md-7 col-sm-6">
        <img class="img-responsive center-block"  style=\"float: left; margin: 0px 0px 15px 15px;vertical-align: middle;\" src=\"%s\">
        </div>
        </div>
        </div>'''%(fname)
        return html
    
    def generateGroupsSidebySideSubjectsPlot():
        for group in groups:
            groupgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.cgroup == group)],rows=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
            groupgrades.unstack()
            studentgrades.reset_index(level=0, inplace=True)
            allgrades = pd.merge(groupgrades,allgrades,on="subject")
    
    
    def promcourseplots(self,period):
        '''
        Generates stacked bar plots of the number of not passed subjects for each course with all the groups on it
        Z    Y     Z
        Y    Y     Y
        X    X     Y
        X    X     X        
        X    X     X
        1A   1B   1C
        '''
        l=("0","1-2","3-4",">=5")                    
        courses = self.df[self.df.year == self.year].coursename.unique()#FIXME excludedCourses?
        for course in courses:
            groups = self.df[(self.df.year == self.year) & (self.df.coursename == course)].cgroup.unique()
            groupsd={}
            groupsc=[]
            for group in groups:
                group1 = group.replace(". ", "")
                group1 = group1.replace("º ", "")
                groupsd[group1]=group
                groupsc.append(group1)
            groupsc.sort()
            #remove "º "  and ". "
            groupslist=[]
            for group in groupsc:
                pt = pd.pivot_table(self.df[(self.df.year == year) & (self.df.period == period) & (self.df.cgroup == groupsd[group])], index=["student"], values=["grade"], aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                p, prom, riesgo, peligro, left, legendhist = self.generatePiedata(missed,{},self.langg)
                a=prom[0],sum(prom[1:]),sum(riesgo),sum(peligro)#prom has only 3 values 0 susp, 1susp and 2 susp, others are 0
                t=sum(a)
                a = [x *100/ t for x in a]
                groupslist.append(a)
            df=pd.DataFrame(groupslist)
            df.columns=l
            df=df.transpose()
            df.columns=groupsc
            df=df.transpose()
            print(df)
            barcolors = ['#6CA439', '#3074AE','orange', 'red']
            df.plot(kind='bar', stacked=True,title=course,color=barcolors,)
            plt.ylim(0, 100)
            plt.legend( loc=8, ncol=4, mode="expand", borderaxespad=0.)
            plt.savefig(self.workdir+"/"+course + '-allgroupsprom.png')
            plt.close()
    
if __name__ == "__main__":
    #db = "/home/asier/Hezkuntza/SGCC/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluacion/Python-educa/test2.db"
    db = "/home/asier/Hezkuntza/python-hezkuntza/Python-educa/test2.db"
    ebaluaketak = ['1. Ebaluaketa', '2. Ebaluaketa', '3. Ebaluaketa', 'Azken Ebaluaketa', 'Ohiz kanpoko Ebaluaketa']
    baliogabekokurtsoak = [b'Programa de Curr\xc3\xadculo Adaptado']
    baliogabekokurtsoak = ['Programa de Currículo Adaptado']
    baliogabekolaburdurak = []
    year = "2015-2016"
    n = notak(db,'eu')
    n.setWorkDir("1ebaluaketa15-16-full3")
    files = ["/home/asier/Hezkuntza/python-hezkuntza/Python-educa/15-16-1eb.csv"]
    #n.insertdataDB(files)
    n.configure(year, ebaluaketak, 1, baliogabekokurtsoak, baliogabekolaburdurak)
    n.removepending()
    stop
    n.promcourseplots("1. Ebaluaketa")
    taldeak = n.df[n.df.year == "2015-2016"].cgroup.unique()
    for t in taldeak:
        n.generateGroupStatsPlots(t)
    n.generateAllGroupStatsPlots()
    taldeak = n.df[n.df.year == "2015-2016"].cgroup.unique()
    for t in taldeak:
        n.generatePassPercent("1. Ebaluaketa","2015-2016",t)
    #n.generatePassPercent("1. Ebaluaketa","2015-2016")
    #a = n.generateStatsSubjectsPandas("2015-2016","1. Ebaluaketa")
    #n.generateStatsStudentPandas("2015-2016", "1. Ebaluaketa")
    n.generateAllGroupPlots(np.mean)
    n.generateAllGroupPlots(n.percent)
    n.generateCoursePlots(np.mean)
    n.generateCoursePlots(n.percent)
    n.generateGroupStatsPlots()
    n.generateCourseStatsPlots()
    print("generate All Stats Plots")
    n.generateAllStatsPlots()
    print("generate STats Student")
    n.generateStatsStudent("2015-2016", "1. Ebaluaketa")#,groups=("Bach.2A","Bach.2B","Batx.2H","Batx.2I","Batx.2J"))
