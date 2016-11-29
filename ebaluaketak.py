# -*- coding: utf-8 -*-
#!/usr/bin/python
from __future__ import division
import sqlite3
import csv
import os
from util import *


class EducaReports:

    periods = []
    html = ""
    workdir = ""
    excludedCourses = []
    dbfile = ""

    def __init__(self, dbfile):
        self.dbfile = dbfile

    def setWorkDir(self, wdir):
        #if wdir doesn't exists create it, else error:
        #No such file or directory, create also workdir+/pics
        self.workdir = wdir + "/"
        self.createDir(self.workdir+"/pics")

    def createDir(self,directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def generatetable(self, conn):
        conn.execute('''CREATE TABLE results
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
        conn.execute('''CREATE TABLE abreviations
            (id INTEGER PRIMARY KEY AUTOINCREMENT    NOT NULL,
            name           TEXT   NOT NULL,
            abv_es        TEXT NOT NULL,
            abv_eu        TEXT  NOT NULL,
            course        INT NOT NULL,
            dept           TEXT NOT NULL);''')
        print("Abreviations table created successfully")

    def insertdata(self, files):
        '''
        Input: A list of csv files with the following format:
        Ikasturtea,Taldea,Kurtso,Hizkuntza eredua,Izen Osoa,Irakasgaiaren Izena,Ebaluaketa,Zenbakizko nota ohikoa
        ['2013-2014', '1. I', '1. DBH', 'D', 'XXXXX', 'Gizarte Zientziak, Geografia eta Historia BH1', '2. Ebaluaketa', '9']
        '''
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        print("Opened database successfully")
        if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='results'").fetchall()[0][0] == 0:
            self.generatetable(cur)
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
                    cur.execute("INSERT INTO results(year, cgroup, course, language, subject, period, student, grade) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], row[3], row[5], row[6], row[4], grade))
        con.commit()
        con.close()

    def insertabr(self, file):
        '''
        Input: A file with the following format:
        Subject,LAB,ABR,course
        Arte eta Teknologia Esparrua 1,ATE,AAT,1
        '''
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        print("Opened database successfully")
        #if cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='results'").fetchall()[0][0] == 0:
        #    generatetable(cur)
        with open(file, 'r') as abrevs:
            reader = csv.reader(abrevs)
            next(reader, None)  # skip first row with headers
            for row in reader:
                cur.execute("INSERT INTO abreviations(name, abv_eu, abv_es, course, dept) VALUES(?, ?, ?, ?, ?)", (row[0], row[1], row[2],row[3],row[4]))
        con.commit()
        con.close()

    def getsubjects(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        subjects = cur.execute("select distinct subject from results").fetchall()
        for subject in subjects:
            print((subject[0]))
        return [s[0] for s in subjects]

    def getyears(self):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        years = cur.execute("select distinct year from results").fetchall()
        for year in years:
            print((year[0]))
        return [a[0] for a in years]

    def getcourses(self, year=None, student=None):
        con = sqlite3.connect(self.dbfile)
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

    def promotionStatsQuery(self, sqln, sqlt, year, ebal):
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        n = cur.execute(sqln, (year, ebal))
        n = n.fetchall()
        n = getColumn(n, 0)
        t = cur.execute(sqlt, (year, ebal))
        t = t.fetchall()
        t = getColumn(t, 0)
        tot = len(t)
        tots = len(n)
        prom = tot - sum(i > 2 for i in n)
        mal = sum(i > 4 for i in n)
        riesgo = tot - prom - mal
        con.close()
        return prom, riesgo, mal

    def generatePromotionStats(self, year, ebal, mod=None, group=None, courses=None):
        '''
        Returns: This function generates the number of students wich promotes,
        are in danger or lost
        And also creates a pie diagram with that data
        year;course;Ebaluaketa;prom;risk;lost
        2007-2008;2. DBH;1. Ebaluaketa;13;0;0
        ...
        '''
        select = "select count(*) from results "

        language = langQuery(mod)
        where = "where year=? and period=?"

        if language:
            where = where + " and " + language
        if courses:
            where = where + " and " + generateOR("course", courses)
        if not language and not courses and group:
            where = where + ' and cgroup="' + group + '"'
        elif not courses:
            con = sqlite3.connect(self.dbfile)
            cur = con.cursor()
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=?", [year]).fetchall() if c[0].encode("utf8") not in self.excludedCourses]
            con.close()
        # FIXME: IF mod is passed and no courses, then it can return, global
        # mod resutls, or results for each course of mod
        sqln = select + where + " and (grade<5 and grade>=0) GROUP BY student"
        sqlt = select + where + " GROUP BY student"
        #  print(sqln)
        #  print(sqlt)
        if courses:
            for course in sorted(courses):
                print(course)
                prom, riesgo, mal = self.promotionStatsQuery(sqln, sqlt, year, ebal)
                title = year + " " + course + "\n" + ebal
                name = self.workdir + course + "-" + str(mod) + "-" + year + "-" + ebal + ".png"
                data = [prom, riesgo, mal]
                piediagram(name, title, data)
                mylis = ';'.join(map(str, [year, course, ebal, prom, riesgo, mal]))
                print(mylis)
        else:
            prom, riesgo, mal = self.promotionStatsQuery(sqln, sqlt, year, ebal)
            mylis = ';'.join(map(str, [year, group, ebal, prom, riesgo, mal]))
            title = year + " " + str(group) + "\n" + ebal
            #str(group) for conversion when group=None
            name = self.workdir + str(group) + "/" + year + "-" + ebal + str(group) +".png"
            data = [prom, riesgo, mal]
            piediagram(name, title, data)
            print(mylis)

    def generatePositiveNegativeGrades(self, ebal, year, mod=None, group=None, courses=None):
        '''
        Returns: This function generates the number of positive, negative and
        no evaluated cases for each subject, and year
        2. DBH
        year;course;Ebaluaketa;subject;positive;negative;null,per
        2007-2008;2. DBH;1. Ebaluaketa;Atzerriko Bigarren Hizkuntza: Frantsesa BH2;13;0;0;%100
        ...
        '''
        print(("courses: ", courses))
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        ebaluaketa = ebal
        select = "select count(*) from results "

        language = langQuery(mod)

        if not courses:
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=?", [year]).fetchall() if c[0].encode("utf8") not in self.excludedCourses]

        if language:
            where = "where year=? and course=? and period=? and subject=?" + " and " + language
        else:
            where = "where year=? and course=? and period=? and subject=?"

        if group:
            where = where + " and cgroup='" + group + "'"
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=? AND cgroup=?", [year, group]).fetchall()]

        sqlp = select + where + " and grade>=5 and grade<=10"
        sqln = select + where + " and (grade<5 and grade>=0)"
        sqlx = select + where + " and (grade<0 and grade>10)"
        #  print (sqlp)
        #  print (sqln)
        #  print (sqlx)
        #  print(year)
        for course in sorted(courses):
            print(course)
            perles70 = 0
            subjectsamount = 0
            perles70subjects = []
            subjects = [s[0] for s in cur.execute("SELECT DISTINCT subject FROM results WHERE year=? AND course=?", (year, course)).fetchall()]
            print((';'.join(["year", "course", "Ebaluaketa", "subject", "positive", "negative", "null"])))
            for subject in sorted(subjects):
               #print(year,course,period,subject)
                p = cur.execute(sqlp, (year, course, ebaluaketa, subject))
                p = p.fetchall()[0][0]
                n = cur.execute(sqln, (year, course, ebaluaketa, subject))
                n = n.fetchall()[0][0]
                x = cur.execute(sqlx, (year, course, ebaluaketa, subject))
                x = x.fetchall()[0][0]
                per = 0
                if p + n + x > 0:
                    per = p * 100 / (p + n + x)
                    subjectsamount += 1
                    if per < 70:  # FIXME 2º Bach bakarrik %60
                        perles70 += 1
                        perles70subjects.append(subject)
                        # FIXME I think the next if block and mylis could be indented so empty sujects not appear
                mylis = ';'.join(map(str, [year, course, ebaluaketa, subject, p, n, x, " %:" + str(per)]))
                if n != 0 or p != 0:
                    print(mylis)
            print((course + ": Subjects with less than %60 of sutdents passed: " + str(perles70) + "-> %" + str(perles70 * 100 / subjectsamount) + ": " + ",".join(map(str, perles70subjects))))
        con.close()

    def generatestatsCourse(self, mod, ebal, syear=None):
        '''
        This function generates stats about the % of positive grades for a evaluation period for each year and subject
        Returns:
        1. Batxilergoa LOE
        Euskal Hizkuntza eta Literatura I;0.6666666666666666;0.8378378378378378;0.9848484848484849;0.8703703703703703
        ....
        '''
        print("GeneratestatsCourse, % of positive grades for each course,subject and year")
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        #periods = cur.execute("SELECT DISTINCT period FROM results").fetchall()  #[('Ohiz kanpoko Ebaluaketa',), ('3. Ebaluaketa',), ('1. Ebaluaketa',), ('2. Ebaluaketa',), ('Azken Ebaluaketa',)]
        #subjects = cur.execute("SELECT DISTINCT subject FROM results").fetchall()
        if syear:
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=?", [syear]).fetchall()  if c[0].encode("utf8") not in self.excludedCourses]
        else:
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results").fetchall()  if c[0].encode("utf8") not in self.excludedCourses]
        #years = cur.execute("SELECT DISTINCT year FROM results").fetchall()
        ebaluaketa = ebal
        select = "select count(*) from results "

        language = langQuery(mod)

        where = "where year=? and course=? and period=? and subject=?" + " and " + language
        sqlp = select + where + " and grade>=5 and grade<=10"
        sqln = select + where + " and (grade<5 and grade>=0)"
        sqlx = select + where + " and (grade<0 and grade>10)"
        #  print (sqlp)
        #  print (sqln)
        #  print (sqlx)
        for course in sorted(courses):
            subjects = cur.execute("SELECT DISTINCT results.subject FROM results,abreviations WHERE results.course=? AND results.subject=abreviations.name AND abreviations.course=?", [course,course[0]]).fetchall()
            if syear:
                years = [(syear,)]
            else:
                years = cur.execute("SELECT DISTINCT year FROM results WHERE course=?", [course]).fetchall()
                #print(';'.join(["year","course","Ebaluaketa","subject","positive","negative","null"]))
            print(course+';'+';'.join(getColumn(years,0)))
            for subject in sorted(subjects):
                mylis = [subject[0]]
                for year in sorted(years):
                    #print(year,course,period,subject)
                    p = cur.execute(sqlp, (year[0], course, ebaluaketa, subject[0]))
                    p = p.fetchall()[0][0]
                    n = cur.execute(sqln, (year[0], course, ebaluaketa, subject[0]))
                    n = n.fetchall()[0][0]
                    x = cur.execute(sqlx, (year[0], course, ebaluaketa, subject[0]))
                    x = x.fetchall()[0][0]
                    # mylis = ';'.join(map(str,[year[0],course[0],'1. Ebaluaketa',subject[0],p,n,x]))
                    # year;course;Ebaluaketa;subject;positive;negative;null
                    # 2007-2008;2. DBH;1. Ebaluaketa;Atzerriko Bigarren Hizkuntza: Frantsesa BH2;13;0;0
                    if n != 0 or p != 0:
                        mylis.append(str(p / (p + x + n)))
                    else:
                        mylis.append("")
                print((';'.join(mylis)))
        con.close()

    def generateGroupStatsGradeAverage(self, year, ebals, course=None, mod=None, groups=None):
        '''
        returns the average grade for each subject
         {u'2H':
             {
             u'Natur Zientziak BH2': {'2. Ebaluaketa': 5.6923076923076925},
             u'Erlijioa BH2': {'2. Ebaluaketa': 7.666666666666667},
             u'Oinarrizko Hizkuntza Trebetasunak BH2': {'2. Ebaluaketa': 4.8},
             u'Matematika sakontzen BH2': {'2. Ebaluaketa': 7.0},
             u'Atzerriko Bigarren Hizkuntza: Frantsesa BH2': {'2. Ebaluaketa': 6.0},
             u'Euskal Hizkuntza eta Literatura BH2': {'2. Ebaluaketa': 5.538461538461538},
             u'Teknologia BH1': {'2. Ebaluaketa': 0.0},
             u'Gaztelania eta Literatura BH1': {'2. Ebaluaketa': 0.0},
             u'Gaztelania eta Literatura BH2': {'2. Ebaluaketa': 5.3076923076923075},
             u'Plastika eta Ikus-hezkuntza BH2': {'2. Ebaluaketa': 5.615384615384615},
             u'Erlijioen historia eta kultura BH2': {'2. Ebaluaketa': 5.5},
             u'Matematika BH2': {'2. Ebaluaketa': 5.653846153846154},
             u'Atzerriko Bigarren Hizkuntza: Alemana BH2': {'2. Ebaluaketa': 4.857142857142857},
             u'Teknologia BH2': {'2. Ebaluaketa': 5.769230769230769},
             u'Gizarte Zientziak, Geografia eta Historia BH2': {'2. Ebaluaketa': 5.346153846153846},
             u'Hezkuntza Arreta BH2': {'2. Ebaluaketa': 6.6923076923076925},
             u'Atzerriko Hizkuntza: Ingelesa BH2': {'2. Ebaluaketa': 5.384615384615385},
             u'Atzerriko Hizkuntza: Ingelesa BH1': {'2. Ebaluaketa': 0.0},
             u'Gorputz Hezkuntza BH1': {'2. Ebaluaketa': 0.0},
             u'Gorputz Hezkuntza BH2': {'2. Ebaluaketa': 6.615384615384615}
             },
         }
        '''
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        #SELECT subject,AVG(grade) FROM results WHERE course='1. Batxilergoa LOE'
        #AND year="2013-2014" AND period="2. Ebaluaketa" AND cgroup="Bach.1A" GROUP BY subject

        language = langQuery(mod)

        if course:
            if language:
                groups = [g[0] for g in cur.execute("SELECT DISTINCT cgroup FROM results WHERE year=? AND period=? AND course=? " + language, [year, ebals[-1], course]).fetchall()]
            else:
                groups = [g[0] for g in cur.execute("SELECT DISTINCT cgroup FROM results WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchall()]
        elif not groups:
            groups = [g[0] for g in cur.execute("SELECT DISTINCT cgroup FROM results WHERE year=? AND period=?", [year, ebals[-1]]).fetchall()]
        gdic = {}
        for group in groups:
            dic = {}
            for period in ebals:
                subjects = cur.execute("SELECT results.subject,AVG(results.grade) FROM results,abreviations WHERE  results.year=? AND results.cgroup=? AND results.period=? AND results.subject=abreviations.name AND abreviations.course=? GROUP BY results.subject", [year, group, period,group[0]]).fetchall()
                for sub in subjects:
                    if sub[0] in list(dic.keys()):
                        dic[sub[0]][period] = sub[1]
                    else:
                        dic[sub[0]] = {}
                        dic[sub[0]][period] = sub[1]
            gdic[group] = dic
        con.close()
        return gdic

    # Pendienteak kurtsoan bertan agertzen dira, 2. batx badu 1. batx pendiente course=2. batx
    def generateStatsStudent(self, year, ebal, mod=None, groups=None):
        '''
        Generates a html file foreach group, which includes a table with each student marks (present and past periods)
        and also a graph with the same data plus a column with the average of the course
        '''
        con = sqlite3.connect(self.dbfile)
        cur = con.cursor()
        ebals = self.periods[:self.periods.index(ebal) + 1]
        legend = [e for e in ebals]
        legend.append("mailaren BB")
        groupsp = groups
        if not groups:
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=? AND period=?", [year, ebals[-1]]).fetchall() if c[0].encode("utf8") not in self.excludedCourses]
        else:
            g = generateOR("cgroup", groups)
            courses = [c[0] for c in cur.execute("SELECT DISTINCT course FROM results WHERE year=? AND period=? AND " + g, [year, ebals[-1]]).fetchall() if c[0].encode("utf8") not in self.excludedCourses]
        for course in sorted(courses):
            print(course)
            subjectsavg = {}
            subjects = [s[0] for s in cur.execute("SELECT DISTINCT results.subject FROM results,abreviations WHERE results.year=? AND results.period=? AND results.course=? AND results.subject=abreviations.name AND abreviations.course=?", [year, ebals[-1], course, course[0]]).fetchall()]
            for subject in subjects:
                avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=? AND subject=?", [year, ebals[-1], course, subject]).fetchone()
                subjectsavg[subject] = str(avg[0])
            avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchone()
            subjectsavg["BB"] = str(avg[0])
            # Use a function wich generates stats for the course
            groups = [g[0] for g in cur.execute("SELECT DISTINCT cgroup FROM results WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchall()]
            if groupsp:
                groups = [g for g in groups if g in groupsp]
            for group in groups:
                self.generateGroupStatsGradeAverage(year, ebals, course, [(group)])
                students = [s[0] for s in cur.execute("SELECT DISTINCT student FROM results WHERE year=? AND period=? AND course=? AND cgroup=?", [year, ebals[-1], course, group]).fetchall()]
                print(group)
                # Use a function wich generates stats for the group
                htmlmenu = ""
                ghtml = ""
                for student in sorted(students):
                    print(student)
                    htmlmenu = htmlmenu + '<li><a href=\"#' + "-".join(str(student).split()) + '\">' + student + '</a></li>'
                    #subjects = [s[0] for s in cur.execute("SELECT DISTINCT subject FROM results WHERE year=? AND period=? AND course=? AND student=?", [year, ebals[-1], course, student]).fetchall()]
                    subjects = [s[0] for s in cur.execute("SELECT DISTINCT results.subject FROM results,abreviations WHERE results.year = ? AND results.period=? AND results.course=? AND results.student=? AND results.subject=abreviations.name AND abreviations.course=?", [year, ebals[-1], course, student,course[0]]).fetchall()]
                    summary = []
                    for subject in subjects:
                        subsum = []
                        #print(subject)
                        subsum.append(subject)
                        for period in ebals:
                            grades = cur.execute("SELECT grade FROM results WHERE year=? AND period=? AND course=? AND student=? AND subject=?", [year, period, course, student, subject]).fetchone()
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
                    subsum = []
                    subsum.append("BB")
                    for period in ebals:
                        avg = cur.execute("SELECT AVG(grade) FROM results WHERE year=? AND period=? AND course=? AND student=?", [year, period, course, student]).fetchone()
                        if avg[0]:
                            subsum.append(str(avg[0]))
                        else:
                            subsum.append(str(0))
                    subsum.append(subjectsavg["BB"])
                    summary.append(subsum)
                    fname = year + "-" + ebal + "-" + student + ".png"
                    if summary != []:
                        cur = con.cursor()
                        for s in summary[:-1]:
                            n = cur.execute("select abv_eu from abreviations where name=?", [s[0]]).fetchone()[0]
                            s[0] = n
                        self.createDir(self.workdir + group)
                        bardiagram(student, self.workdir + group +"/" + fname, summary, legend)
                    html = ""
                    html = html + '''
                    <div class="student">
                        <h1 style=\"clear: both;\" id='%s'></h1>
                        <h1> %s  <a href=#top>(^)</a></h1>
                        <div class="row" style=\"display: flex; align-items: center;\">
                        <div class="col-md-3 col-sm-3">
                        <table class=\"table table-striped\" border="1" text-aling="center">
                            <tr>
                                <th>Ikasgaia</th>'''%("-".join(str(student).split()),student)
                    for e in ebals:
                        html = html + "<th>" + e + "</th>\n"
                    html = html + "</tr>\n"
                    for s in summary:
                        if len(summary)>2 and float(s[-3])>float(s[-2]):
                            html = html + "<tr class=\"danger\">"
                        elif float(s[-3])<float(s[-2]):
                            html = html + "<tr class=\"success\">"
                        else:
                            html = html + "<tr>"
                        for a in s[:-1]:
                            html = html + "<td>" + a + "</td>\n"
                        html = html + "</tr>\n"
                    html = html + '''</table>
                    </div>
                    <div class="col-md-7 col-sm-6">
                    <img style=\"float: left; margin: 0px 0px 15px 15px;vertical-align: middle;\" src=\"%s/%s\">
                    </div>
                    </div>
                    </div>'''%(group,fname)
                    #print(html)
                    #f = open(self.workdir + group + "/" + fname + ".html", 'w')
                    #f.write("<html><head><meta charset=\"utf-8\"></head><body>" + html.encode("utf8") + "</body></html>")
                    #f.close()
                    ghtml = ghtml + html
                self.generatePromotionStats(year, ebal, group=group)
                pie = str(group) + "/" + year + "-" + ebal + str(group) + ".png"
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
                        <div class=\"row\">
                            <div class=\"col-sm-3 col-md-2 sidebar\">
                                <ul class=\"nav nav-sidebar\">
                                %s
                                </ul>
                            </div>
                            <div class=\"col-sm-9 col-sm-offset-3 col-md-10 col-md-offset-2 main\">
                                <h1 class=\"page-header\" id=top>Taldeko emaitzak</h1>
                                <img src=\"%s\">
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
                </html>"
                '''%(htmlmenu,pie,ghtml)
                f = open(self.workdir + group + ".html", 'w')
                f.write(ghtml) #  f.write(ghtml.encode("utf8"))
                f.close()

if __name__ == "__main__":
    er = EducaReports("test2.db")
    er.insertabr("laburdurak.csv")
    er.setWorkDir("2ebaluaketa")
    #files = ["0708.csv", "0809.csv", "0910.csv", "1011.csv", "1112.csv", "1213.csv", "1314.csv"]
    files = ["14-15-2eb8.csv"]
    #er.insertdata(files)
    er.periods = ['1. Ebaluaketa', '2. Ebaluaketa', '3. Ebaluaketa', 'Azken Ebaluaketa', 'Ohiz kanpoko Ebaluaketa']
    er.excludedCourses = ["1. Oinarrizko Hezkuntza (C.E.U.)","2. C.E.U.","3. C.E.U","4. C.E.U.","Programa de Currículo Adaptado"]
    #er.generatestatsCourse('D', '1. Ebaluaketa')
    #er.generatestatsCourse('AG', '2. Ebaluaketa')
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2013-2014", courses=[("2. Batxilergoa LOE")])
    #er.generatePositiveNegativeGrades("1. Ebaluaketa", "2013-2014", group="2. J")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2013-2014", courses=[("2. Batxilergoa LOE")], mod='D')
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2013-2014", courses=[("2. Batxilergoa LOE")], mod='AG')
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2013-2014")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")])
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")], mod='AG')
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", group="Bach.2A")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", group="Bach.2B")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", group="Bach.2C")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")], mod='D')
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", group="Batx.2H")
    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015", group="Batx.2I")

#Generar quesitos:
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")])
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")], mod='AG')
    #er.generatePromotionStats("2014-2015", "2. Ebaluaketa", group="Bach.2A")
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", group="Bach.2B")
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", group="Bach.2C")
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", courses=[("2. Batxilergoa LOE")], mod='D')
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", group="Batx.2H")
    #er.generatePromotionStats("2. Ebaluaketa", "2014-2015", group="Batx.2I")

    #er.generatePositiveNegativeGrades("2. Ebaluaketa", "2014-2015")
    #er.generatestatsCourse("D", "2. Ebaluaketa")
    #er.generatestatsOp("D", "2. Ebaluaketa")

#Generar hojas de alumnos
#    er.generateStatsStudent('2014-2015', '2. Ebaluaketa', groups=["Bach.2A", "Bach.2B", "Batx.2I", "Batx.2H"])
    #er.generateStatsStudent('2014-2015', '2. Ebaluaketa', groups=['4A', '2º A', '2º B', '2º D', 'Bach.1A', '3A', '1º C', '4D', 'Batx.1J', '3C', 'Bach.2A', '3D', '1. H', '1º A', 'Batx.1I', '4H', '3B', '3K', '2º C', '4B', '2. H', '1. I', '1. K', 'Bach.2C', '4C', '4Q', '2. I', '1. J', '2. K', '1º D', 'Bach.2B', '3J', 'Batx.2I', '4L', '3P', '1º B', '3H', '4J', 'Batx.1H', 'Bach.1B', '4I', '2. J', '3I', 'Batx.2H', '4K', '4P', '1º E', '3Q', '2º E'])
    #er.generateStatsStudent('2014-2015', '2. Ebaluaketa')
    print("Here")
    #print(er.generateGroupStatsGradeAverage('2012-2013',['2. Ebaluaketa'], mod='AG', groups=['2H']))
    #er.generatePromotionStats('2013-2014', '1. Ebaluaketa', courses=["2. Batxilergoa LOE"], mod="AG")
    #er.generatePromotionStats('2013-2014', '1. Ebaluaketa', mod="D")
    #er.generatePromotionStats('2013-2014', '1. Ebaluaketa', courses=["2. Batxilergoa LOE"], mod="A")
    #er.generatePromotionStats('2013-2014', '1. Ebaluaketa', courses=["2. Batxilergoa LOE"], mod="G")
    #er.generatePromotionStats('2013-2014', '1. Ebaluaketa', group="Batx.2I")
    #er.generatePromotionStats('2013-2014', '2. Ebaluaketa', group="Batx.2I")
    #er.generatePromotionStats('2013-2014', 'Azken Ebaluaketa', group="Batx.2I")
    #er.generatePromotionStats('2013-2014', 'Ohiz kanpoko Ebaluaketa', group="Batx.2I")