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
#plt.style.use('ggplot')
from cycler import cycler
import textdoc as td
rcParams.update({'figure.autolayout': True}) #TODO it makes small plots with very big labels, I've to figure how to change subject names with abreviations
# in each? plt.gca().tight_layout()


class notak:


    barcolors = ['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3']
    plt.rc('axes', facecolor='#FFFEEE', edgecolor='#4E3629')
    plt.rc('patch', facecolor='#6CA439', edgecolor='#517B2B', linewidth=0)
    plt.rc('figure', figsize=(16,6))
    plt.rc('font', size=14.0)
    plt.rc('axes', prop_cycle=(cycler('color',barcolors)))
    plt.rc('lines', linewidth=4)    
    pd.options.display.float_format = '{:,.1f}'.format
    
    def __init__(self, db, lang='es', debug=False):
        """
        Initiates the class
        
        :param db: the sqlite3 db file path
        :param lang: the language of the generated reports (default es-spanish, other option eu-basque)
        :param debug: If the program will print debug messages (default False)
        :return: None
        """
        self.db = db
        self.debug=debug
        self.td = ''
        self.periods = []
        self.workdir = ""
        self.year = ""
        self.langg = lang
        self.subjectsavg = defaultdict(defaultdict)
        self.subjects = {'eu': 'Ikasgaiak','es':'Asignaturas'}
        self.studpasstitle = {'eu': 'Ikasle vs ez gainditutakoak','es':'Alumnos vs suspensos'}
        self.promttitle = {'eu':'Promozioa','es':u'Promoción'}
        self.cur= {'eu':'Oraingoa','es':'Actual'}
        self.prev= {'eu':'Aurrekoa','es':'Anterior'}
        self.avg= {'eu':'BB','es':'Prom'}
        self.avg5 = {'eu':'BB5u','es':'Prom5a'}
        self.langt = {'eu':'Eredu-maila','es':'Modelo-nivel'}
        
        
        self.summary = {'eu':" Taldeko emaitzak",'es':"Resumen del grupo"}
        self.gresults = {'eu':"Taldeko emaitzak",'es':"Resultados del grupo"}
        self.notpas = {'eu':"Ikasleen suspentso kopurua eta notaren Batazbestekoa",'es':"Número de suspensos y nota media de los alumnos"}
        self.average = {'eu':"Batazbestekoa",'es':"Promedio"}
        self.paspercent = {'eu':"Gaindituen ehunekoak",'es':"Porcentajes de aprobados"}
        self.more70 = {'eu':"ehuneko 70 baino gainditu gutxiago duten ikasgaiak",'es':"Asignaturas con menos del 70 por ciento de aprobados"}
        self.sresults = {'eu':"Ikasleen emaitzak",'es':"Resultados de los alumnos"}
        self.groupstats = {'eu':"Taldearen adierazleak",'es':"Indicadores del grupo"}
         
        self.header = "/home/asier/Hezkuntza/SGCC/PR04 Gestion documental/Plantillas - Logos - Encabezados/membrete.png"
        self.footer = ""
        
        html = ""
        


    def getData(self, year, periods, period=1, excludedCourses=[]):
        """
        Configures course and group ploting
        
        :param year: The year whose marks will be plotted
        :param periods: Evaluative period list
        :param period: Current period as int (as index+1 for the list)
        :param excludedCourses: Courses that won't generate a plot
        :return: None, it creates the dataframe with the data from the database
        """
        self.year = year
        self.periods = periods
        self.period = period
        if self.period > len(self.periods):#FIXME: raise ValueError
            raise IndexError("Error: period number > len(periods)")
        notcourses = "NOT grades.course = '" + ("' AND NOT grades.course = '").join(
            excludedCourses) + "'"  # The query works if excludedCourses = []
        ebselect = "grades.period = '" + ("' OR grades.period = '").join(
            self.periods[:self.period]) + "'"
        con = sqlite3.connect(self.db)
        sql="SELECT yeardata.year, yeardata.course AS coursename, yeardata.cgroup, yeardata.lang,\
            yeardata.uniquename, names.fullname, names.primaryschool, \
            grades.subject, grades.code, grades.period, grades.grade \
        FROM \
            yeardata,grades,names \
        WHERE \
            yeardata.year=grades.year AND yeardata.uniquename=grades.uniquename \
            AND yeardata.uniquename=names.uniquename \
            AND yeardata.course=grades.course \
            AND NOT (grades.grade='') AND (" + notcourses + ") \
            AND (" + ebselect + ")"
        if self.debug:
           print(sql)
        self.df = pd.read_sql(sql,con)
        self.df.grade = self.df.grade.astype(int)
        if self.debug:
           print(self.df.head())
        sqlsubjects = "SELECT * FROM subjects WHERE " + "NOT course = '" + ("' AND NOT course = '").join(
            excludedCourses) + "'"
        if self.debug:
           print(sqlsubjects)
        dfsubjects = pd.read_sql(sqlsubjects,con)
        dfsubjects.sort_values('id',inplace=True)
        dfsubjects.drop_duplicates(subset='code',keep='last',inplace=True) #FIXME: Not sure if it gets the last \
        #    because it depends on the database index
        con.close()
        self.df = pd.merge(self.df,dfsubjects,on="code",how="left")#FIXME: Somethin more global would be right . Maybe there's still to much data (columns)
        self.df['bil'] = self.df['lang'].map(self.modeloBil)
        self.df['lang'] = self.df['lang'].map(self.modelo)
        if self.debug:
           print(self.df.head())

    def generateFinalGrade(self):
        '''
        This function geneates new rows with the final grade for each year-studet-subject
        This final grade is the las ordinary one if passed or the extraordinary one.
        '''
        grouped = self.df[(self.df.period=="Ohiz kanpoko Ebaluazioa")|(self.df.period=="Azken Ebaluazioa")].groupby(['year','uniquename','subject'])
        newrows = grouped.apply(self.finalgrade)
        self.df = pd.concat([self.df,newrows])
        self.df.reset_index(drop=True,inplace=True)
        return newrows #Not needed, interesting for testing?

    def finalgrade(self,x):
        if 'Ohiz kanpoko Ebaluazioa' in x[["period","grade"]].period.unique():
            df = x[x.period=="Ohiz kanpoko Ebaluazioa"]
            df.period = "Final"
            return df
        else:
            df = x[x.period=="Azken Ebaluazioa"]
            df.period = "Final"
            return df

    def generatepending(self):
        """
        Generates a pandas dataframe with pending subjects (the ones not passed from the previous course)
        
        :return: None
        """
        self.dfp = df[df.coursename!=df.ycourse]

    def removepending(self):
        """
        Removes pending subjects (the ones wich course is not the students course) from the dataframe
        
        :return: None
        """
        self.df = self.df[self.df.coursename==self.df.ycourse]

    def setWorkDir(self, wdir):
        # if wdir doesn't exists create it, else error:
        # No such file or directory, create also workdir+/pics
        self.workdir = wdir + "/"
        self.createDir(self.workdir)

    def createDir(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def percent(self, x, n=5):
        """
        :param x: list with grades (0-10)
        :return: The % of >=5 marks (from 10) in a list x
        """
        return sum(1 for a in x if a >= n) * 100 / len(x) if len(x) != 0 else ''

    def lowerThan(self,x,n=5):
        '''        
        :param x: list with grades (0-10)
        :return: the amount of values in the list x that are less than n (default 5)
        '''
        return sum(1 for a in x if a < n)

    def modelo(self, x):
        """
        :param x: list with course language
        :return: D for D and AG for A or G
        """
        if x == 'D':
            return 'D'
        elif x in ['A','G','G-A.Eleb.In.','A-A.Eleb.In.','G-A.Elea.','A-A.Elea.']:
            return 'AG'

    def modeloBil(self, x):
        """
        :param x: list with course language
        :return: D for D and AGBil or AGPlur for A or G with english program
        """
        if x == 'D':
            return 'D'
        elif x in ['A','G']:
            return 'AG'
        elif x in ['G-A.Eleb.In.','A-A.Eleb.In.']:
            return 'AGbil'
        elif x in ['G-A.Elea.','A-A.Elea.']:
            return 'AGPlur'


    def generatesheet(self, group):
        """
        Generates a table with the grades for each student and subject
        for the configured year and period
        Only for current year and eb'
        
        :param group: Name of the group
        """
        return pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.period - 1])], index=["uniquename"], values=["grade"],
                              columns=["subject"]).fillna('')


    def notPassedStats(self,dfgrades):
        """
        From a list returns a dic with the number of not passed subjects and students
        
        :param dfgrades: a grades series with names as index 
        uniquename
        
        aabadiacaj     0
        
        aalvardiaz     0
        
        acarvalper     8
        
        agarciacha     0
        
        ajimenemen2    0
        
        aruedasbal     2
        
        ausandilor     0
        ...
        
        :return gradescount: a dic with the number of not passed subjects and student number
        defaultdict(<class 'int'>, {0: 10, 1: 5, 2: 5, 3: 3, 4: 1, 5: 2, 6: 1, 8: 3})
        """
        gradescount = defaultdict(int)
        for y in dfgrades:
            gradescount[y] += 1
        return gradescount


    def perioddata(self,year,period):
        '''
        FIXME:this function is never called
        '''
        con = sqlite3.connect(self.db)
        df = pd.read_sql("select yeardata.year,yeardata.course,yeardata.cgroup,yeardata.lang,yeardata.uniquename,grades.subject,grades.period,grades.grade from yeardata,grades where yeardata.year=grades.year and yeardata.uniquename=grades.uniquename and grades.course=yeardata.course and yeardata.year='"+year+"' and grades.period='"+period+"'",con)
        return df

    def getGroupPromStats(self,group):
        '''
        Generates stats about failures in the specified group, for the configured year and period
        [66.66666666666667, 13.333333333333334, 20.0], 2.2666666666666666
        
        :param group: name of the group
        :return: p - a list with the percent of students in each situation (promoting <= 2 susp, risk 3-4 susp, danger > 4 susp) and the average of fails for students
        '''
        pt = pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.period - 1])], index=["uniquename"], values=["grade"],
                          aggfunc=self.lowerThan).fillna('')
        if self.debug:
           print("Get data for group: " + group)
           print(pt)
        missed = self.notPassedStats(pt.grade)
        p,prom,risk,danger, left,legendhist = self.generatePiedata(missed)
        studentnumber = sum(p)
        p = [value*100/studentnumber for value in p]
        failsnumber = sum([i*f for i,f in enumerate(prom)])+sum([i*f for i,f in enumerate(risk)])+sum([i*f for i,f in enumerate(danger)])
        average = failsnumber/studentnumber
        return p,average

    def askabitutorinfo(self):
        con = sqlite3.connect(self.db)
        df = pd.read_sql("select giroa, material, cleaness, studentstudent, studentteacher, period, cgroup from tutorinfo",con)
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            p,m=self.getGroupPromStats(group)  
        return df

    def generatePlot(self,diagram,func,coursegroup):
        '''
        Generates a bar plot from the diagram dataframe
        
        :param diagram: Dataframe with the data to be ploted
        :param func: it can be the average of the grades (mean) or the percentaje of passed for each subject
        :param coursegroup: only needed to create the filename
        :return figurefile: The name of the stored plot (not the path)
        '''
        gtitle = coursegroup + ' - ' + self.periods[self.period - 1] + " (" + self.year + ") "
        diagram.plot(kind='bar', title=gtitle).legend(loc=4)
        plt.title(gtitle)
        if func.__name__ == 'mean':
            plt.ylim(0, 10)
            plt.axhline(5)
        else:
            plt.ylim(0, 100)
            plt.axhline(70)
        figurefile = gtitle + '-' + func.__name__ + '-'+self.langg+'.png'
        plt.savefig(self.workdir+"/"+figurefile)
        plt.close()
        return figurefile
   
    def generatePiePlot(self,missed,name):
        '''
        Generates a pie plot from the missed list
        
        :param missed: a list with the number of students for each number of not passed subjectcs
        :param name: the name for the title of the diagram
        :return: None, it stores the plot in the filesystem
        '''
        p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
        title= self.studpasstitle[self.langg]
        title2 = self.promttitle[self.langg]
        if self.debug:
          print(name+";"+str(sum(prom))+";"+str(sum(peligro)))
        t = sum(p)
        p = [x *100/ t for x in p]
        legendpie = ("<=2","3-4","=>5")
        colors = ['#6CA439', '#FF9C42', '#FF4848']
        plt.suptitle(name, fontsize=14)
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
        filename = self.workdir + "/" + name + "-" + self.periods[self.period-1] + "-" + self.langg + ".png"
        plt.savefig(filename)
        plt.close()
        return p,prom,riesgo,peligro,filename
   
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
                lang='All'
            for course in dflang[dflang.year == self.year].course.unique():#FIXME: Change in other functions coursename for course. Coursename has LOMCE, course not
                if self.debug:
                   print(self.year, course,dflang[dflang.year == self.year].course.unique())
                if course == pd.np.nan:
                    continue
                coursedf = dflang[dflang['course'] == course]
                courseyearebspivot = pd.pivot_table(coursedf, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot =courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                selectperiods = courseyearebspivot.swaplevel(0, 2, axis=1)
                selectyears = courseyearebspivot.swaplevel(0, 1, axis=1)
                currenteb = selectperiods[self.periods[self.period - 1]]
                
                years = coursedf.year.unique()
                years.sort()
                years = years[-6:] if len(years) > 6 else years
                
                currenttext =  "(" + course + "-" + lang + ")" + self.cur[self.langg]
                prevtext = "(" + course + "-" + lang + ")" + self.prev[self.langg]
                avg5text = "("+ course + "-" + lang + ")" + self.avg5[self.langg]
                
                diagram = pd.DataFrame()
                diagram[currenttext] = currenteb[currenteb.keys()[-1]]
                if len(years) == 1:
                   diagram[avg5text] = currenteb[years].mean(axis=1)
                else:
                   diagram[avg5text] = currenteb[years[:-1]].mean(axis=1)
                if self.period not in  [1,6]:
                    previouseb = selectperiods[self.periods[self.period - 2]]
                    diagram[prevtext] = previouseb[previouseb.keys()[-1]]
                    diagram=diagram[[prevtext,currenttext,avg5text]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[prevtext].mean(), diagram[currenttext].mean(), diagram[avg5text].mean())],
                                     index=[self.avg[self.langg]], columns=[prevtext, currenttext, avg5text]))
                else:
                    diagram=diagram[[currenttext,avg5text]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[currenttext].mean(), diagram[avg5text].mean())], index=[self.avg[self.langg]],
                                     columns=[currenttext, avg5text]))
                gtitle = course + '-' + lang
                
                self.generatePlot(diagram,func,gtitle)


    def generateCourseBilPlots(self, func):
        """
        #FIXME: Description
        This function generates plots for each course with bilingual classess¿: One for AG languages, another for D and?
        the last one for all of them for current year and period
        If the period is not the first, plots have a series with the previous period
        All plots have a series with the average of the last "5" years
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        #dfyearscourses = self.df[self.df.bil=="AGbil"][["course","year"]].drop_duplicates() #gets courses and all years with bil
        #for l in ['AGBil','AGPlur']:
        dfcourses = self.df[(self.df.bil=="AGbil")&(self.df.year==self.year)][["course","lang"]].drop_duplicates()
        for lang in list(dfcourses.lang.unique())+[None]:  # [df.lang.unique(),None]:
            print(lang)
            if lang:
                dflang = self.df[self.df['lang'] == lang]
            else:
                dflang = self.df
                lang='All'
            for course in dflang[(dflang.year == self.year) & (dflang.bil=="AGbil")].course.unique():#FIXME: Change in other functions coursename for course. Coursename has LOMCE, course not
                if self.debug:
                   print(self.year, course)
                bilcoursedf = dflang[(dflang.course == course) & (dflang.bil=="AGbil")]
                courseyearebspivot = pd.pivot_table(bilcoursedf, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot =courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                selectperiods = courseyearebspivot.swaplevel(0, 2, axis=1)
                selectyears = courseyearebspivot.swaplevel(0, 1, axis=1)
                currenteb = selectperiods[self.periods[self.period - 1]]
                
                years = bilcoursedf.year.unique()
                years.sort()
                years = years[-6:] if len(years) > 6 else years
                
                currenttext =  "(" + course + "-" + lang + "-Bil)" + self.cur[self.langg]
                prevtext = "(" + course + "-" + lang + "-Bil)" + self.prev[self.langg]
                avg5text = "("+ course + "-" + lang + "-Bil)" + self.avg5[self.langg]
                
                diagram = pd.DataFrame()
                diagram[currenttext] = currenteb[currenteb.keys()[-1]]
                if len(years) == 1:
                   diagram[avg5text] = currenteb[years].mean(axis=1)
                else:
                   diagram[avg5text] = currenteb[years[:-1]].mean(axis=1)
                if self.period  not in  [1,6]:
                    previouseb = selectperiods[self.periods[self.period - 2]]
                    diagram[prevtext] = previouseb[previouseb.keys()[-1]]
                    diagram=diagram[[prevtext,currenttext,avg5text]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[prevtext].mean(), diagram[currenttext].mean(), diagram[avg5text].mean())],
                                     index=[self.avg[self.langg]], columns=[prevtext, currenttext, avg5text]))
                else:
                    diagram=diagram[[currenttext,avg5text]]
                    diagram = diagram.append(
                        pd.DataFrame([(diagram[currenttext].mean(), diagram[avg5text].mean())], index=[self.avg[self.langg]],
                                     columns=[currenttext, avg5text]))
                gtitle = course + '-' + lang + '-Bil'
                
                self.generatePlot(diagram,func,gtitle)

    def generateCourseBilvsCooursePlots(self, func):
        """
        #FIXME: Description
        This function generates plots for each course with bilingual classess vs The whole course
        the last one for all of them for current year and period
        It only takes the current period
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        #dfyearscourses = self.df[self.df.bil=="AGbil"][["course","year"]].drop_duplicates() #gets courses and all years with bil
        dfcourses = self.df[(self.df.bil=="AGbil")&(self.df.year==self.year)][["course","lang"]].drop_duplicates()
        for lang in list(dfcourses.lang.unique())+[None]: 
            if lang:
                dflang = self.df[(self.df.lang == lang) & (self.df.year == self.year)]
            else:
                dflang = self.df[self.df.year == self.year]
                lang='All'
            for course in dflang[dflang.bil=="AGbil"].course.unique():#FIXME: Change in other functions coursename for course. Coursename has LOMCE, course not
                if self.debug:
                   print(self.year, course)
                bilcoursedf = dflang[(dflang.course == course) & (dflang.bil=="AGbil")  & (dflang.period==self.periods[self.period - 1])]
                bilcourseyearebspivot = pd.pivot_table(bilcoursedf, index=["abv_"+self.langg+""], values=["grade"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                bilcourseyearebspivot =bilcourseyearebspivot[bilcourseyearebspivot[bilcourseyearebspivot.columns[len(bilcourseyearebspivot.columns)-1]].notnull()]
                
                notbilcoursedf = dflang[(dflang.course == course) & (dflang.bil!="AGbil") & (dflang.period==self.periods[self.period - 1])] 
                notbilcourseyearebspivot = pd.pivot_table(notbilcoursedf, index=["abv_"+self.langg+""], values=["grade"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                notbilcourseyearebspivot =notbilcourseyearebspivot[notbilcourseyearebspivot[notbilcourseyearebspivot.columns[len(notbilcourseyearebspivot.columns)-1]].notnull()]
                
                coursedf = dflang[(dflang.course == course)  & (dflang.period==self.periods[self.period - 1])]
                courseyearebspivot = pd.pivot_table(coursedf, index=["abv_"+self.langg+""], values=["grade"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot =courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                
                diagram = pd.merge(courseyearebspivot,bilcourseyearebspivot,left_index=True,right_index=True,suffixes=("_All","_SSBB"))
                diagram = pd.merge(diagram,notbilcourseyearebspivot,left_index=True,right_index=True,suffixes=("","_NoSSBB"))
                diagram.columns = ["Todo el curso","SSBB","sin SSBB"]
                diagram.index.names = [self.subjects[self.langg]]
                
                gtitle = course + '-' + lang + '-Bil'
                
                self.generatePlot(diagram,func,gtitle)

    def generatePrymarySchoolPlots(self, func):
        """
        #FIXME: Description
        This function generates plots for the first course and each original school
        the last one for all of them for current year and period
        It only takes the current period
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        #dfyearscourses = self.df[self.df.bil=="AGbil"][["course","year"]].drop_duplicates() #gets courses and all years with bil
        course = '1 ESO'
        for lang in self.df[(self.df.year==self.year) & (self.df.period==self.periods[self.period - 1]) & (self.df.course==course)].lang.unique():  #FIXME: Coursee hardcoded
            if lang:
                dflang = self.df[(self.df.lang == lang) & (self.df.year == self.year) & (self.df.period==self.periods[self.period - 1]) & (self.df.course== course)]
                if self.debug:
                   print(self.year, course)
                coursedf = dflang
                courseyearebspivot = pd.pivot_table(coursedf, index=["abv_"+self.langg+""], values=["grade"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot = courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                
                for ps in dflang.primaryschool.unique():
                    if ps == None:
                        continue
                    schoolcoursedf = dflang[dflang.primaryschool == ps] 
                    schoolcourseyearebspivot = pd.pivot_table(schoolcoursedf, index=["abv_"+self.langg+""], values=["grade"],aggfunc=func)
                    #Remove subjects that are not in the current period/course
                    schoolcourseyearebspivot =schoolcourseyearebspivot[schoolcourseyearebspivot[schoolcourseyearebspivot.columns[len(schoolcourseyearebspivot.columns)-1]].notnull()]
                
                    diagram = pd.merge(schoolcourseyearebspivot,courseyearebspivot,left_index=True,right_index=True,suffixes=("_"+ps,"_All"))
                    diagram.columns = [ps,"Todos",]
                    diagram.index.names = [self.subjects[self.langg]]
                    
                    gtitle = course + '-' + lang + '-' + ps
                    
                    barplot = self.generatePlot(diagram,func,gtitle)
                    
                    pt = pd.pivot_table(schoolcoursedf, index=["uniquename"], values=["grade"],aggfunc=self.lowerThan).fillna('')
                    missed = self.notPassedStats(pt.grade)
                    p,prom,riesgo,peligro,pietitle = self.generatePiePlot(missed,ps+" ("+lang+")")
                                        
                    doc = td.textdoc()
                    doc.addTitle(ps + " (" + lang + ")")
                    doc.addParagraph("Resumen de las calificaciones obtenidas en 1º ESO en el IES Mendillorri")
                    doc.addTitle2("Resumen de asignaturas")
                    doc.addParagraph("Comparativa datos de los alumnos de las escuela y la media de 1º ESO")
                    doc.addImage(self.workdir + "/" + barplot,"resumen de calificaciones")
                    
                    ptall = pd.pivot_table(schoolcoursedf, index=["fullname"], columns=["name_eu"],values=["grade"]).fillna('')
                    ptavg = pd.pivot_table(schoolcoursedf, index=["fullname"],values=["grade"],aggfunc=np.mean).fillna('')
                    ptsusp = pd.pivot_table(schoolcoursedf, index=["fullname"],values=["grade"],aggfunc=self.lowerThan).fillna('')
                    pt = pd.merge(ptall,ptavg,left_index=True,right_index=True)
                    pt = pd.merge(pt,ptsusp,left_index=True,right_index=True)
                    pt.append(pt.mean(), ignore_index=True)
                    pt.reset_index(inplace=True)
                    doc.addTable(pt.values,["Nombre"]+[i[1] for i in pt.columns[1:-2]]+["media","n susp"])                    
                    doc.addTitle2("Datos de aprobados y promoción")
                    doc.addParagraph("Número de suspensos por alumno y situación de promoción")
                    doc.addImage(pietitle,"resumen de promoción")
                    doc.addImageHeaderFooter("/home/asier/Hezkuntza/SGCC/PR04 Gestion documental/Plantillas - Logos - Encabezados/membrete.png","")
                    self.createDir(self.workdir + "/primaryschool/")
                    doc.save(self.workdir + "/primaryschool/" +ps+lang+".odt")  #FIXME: os.path.join


    def generateDeptPlots(self, func):
        """
        This funcition generates 3 plots for each course: One for AG languages, another for D and
        the last one for all of them for current year and period
        If the period is not the first, plots have a series with the previous period
        All plots have a series with the average of the last "5" years
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        depts = self.df.dept.unique()
        for dept in depts:
            if dept == None or str(dept) == 'nan':
                continue
            doc = td.textdoc()
            doc.addImageHeaderFooter(self.header,self.footer)
            print(dept)
            dept = str(dept)
            doc.addTitle("Departamento: " + dept)
            doc.addParagraph("Este documento contiene un resumen de las calificaciones del departamento.")
            doc.addParagraph("Contiene 3 apartados con la media de las calificaciones de cada asignatura del departamento y con el porcentaje de alumnos aprobados de cada una de ellas, comparado con la media de los últimos 5 años. El primero de ellas de ambos modelos juntos, los dos siguientes con los de AG y D por separado.")
            for lang in [None,'AG', 'D']:  # [df.lang.unique(),None]:
                if lang:
                    dflang = self.df[self.df['lang'] == lang]
                else:
                    dflang = self.df
                    lang='All'
                doc.addTitle2("Modelo:  " + lang )
                deptdf = dflang[dflang.dept == dept].sort_values(by="code")
                datatable = None
                for sfunc in func:
                    deptyearebspivot = pd.pivot_table(deptdf, index=["abv_"+self.langg+""], values=["grade"], columns=['year','period'],aggfunc=sfunc)
                    #Remove subjects that are not in the current period/course
                    deptyearebspivot =deptyearebspivot[deptyearebspivot[deptyearebspivot.columns[len(deptyearebspivot.columns)-1]].notnull()]
                    selectperiods = deptyearebspivot.swaplevel(0, 2, axis=1)
                    selectyears = deptyearebspivot.swaplevel(0, 1, axis=1)
                    currenteb = selectperiods[self.periods[self.period - 1]]
                    
                    years = deptdf.year.unique()
                    years.sort()
                    years = years[-6:] if len(years) > 6 else years
                    
                    currenttext =  "(" + dept + "-" + lang + ")" + self.cur[self.langg]
                    prevtext = "(" + dept + "-" + lang + ")" + self.prev[self.langg]
                    avg5text = "("+ dept + "-" + lang + ")" + self.avg5[self.langg]
                    
                    diagram = pd.DataFrame()
                    diagram[currenttext] = currenteb[currenteb.keys()[-1]]
                    if len(years) == 1:
                        diagram[avg5text] = currenteb[years].mean(axis=1)
                    else:
                        diagram[avg5text] = currenteb[years[:-1]].mean(axis=1)
                    if self.period  not in  [1,6]:
                        previouseb = selectperiods[self.periods[self.period - 2]]
                        diagram[prevtext] = previouseb[previouseb.keys()[-1]]
                        diagram=diagram[[prevtext,currenttext,avg5text]]
                        diagram = diagram.append(pd.DataFrame([(diagram[prevtext].mean(), diagram[currenttext].mean(), diagram[avg5text].mean())],
                                        index=[self.avg[self.langg]], columns=[prevtext, currenttext, avg5text]))
                    else:
                        diagram=diagram[[currenttext,avg5text]]
                        diagram = diagram.append(pd.DataFrame([(diagram[currenttext].mean(), diagram[avg5text].mean())], index=[self.avg[self.langg]],
                                        columns=[currenttext, avg5text]))
                    gtitle = dept + '-' + lang
                    barplot = self.generatePlot(diagram,sfunc,gtitle)
                    doc.addImage(self.workdir + "/" + barplot,"resumen de calificaciones"+lang)
                    diagram = diagram.round(2)
                    diagram.columns = sfunc.__name__ + diagram.columns
                    if datatable is None:
                        datatable = diagram
                    else:
                        datatable = pd.merge(datatable,diagram,left_index=True,right_index=True)
                dfs = self.df[["name_"+self.langg,"abv_"+self.langg,"code"]]
                dfs.drop_duplicates(subset='code',keep='last',inplace=True)
                dfs.drop("code",axis=1,inplace=True)
                datatable = pd.merge(datatable,dfs,right_on="abv_"+self.langg,left_index=True)#FIXME: I'm trying to have the abreviations in the plot and text in the table. IF it works abv_es has to be considered
                datatable.set_index("name_"+self.langg,drop=True,inplace=True)
                datatable.drop("abv_"+self.langg,inplace=True,axis=1)
                doc.addTable(datatable.reset_index().values,["Asignatura"]+list(datatable.columns))
            self.createDir(self.workdir+"/depts")
            doc.save(self.workdir+"/depts/"+dept+".odt") #FIXME: os.path.join


    def generateGroupPlots(self, group, func):
        """
        This function generates a plot for the group with the grades/pass% of each subject depending on func
        If the period is not the first, plots have a series with the previous period
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        if self.debug:
           print(self.year, group)
        #Get course/level infor
        lang = self.df[(self.df.year == self.year) & (self.df.cgroup == group)].lang.unique()[0]
        course = self.df[(self.df.year == self.year) & (self.df.cgroup == group)].course.unique()[0]
        if self.debug:
           print("Eredua: ",lang)
        levelpivot = self.df[(self.df['lang'] == lang) & (self.df['year'] == self.year) & (self.df['course'] == course)]
        levelpivot = pd.pivot_table(levelpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        levelperiods = levelpivot.swaplevel(0, 2, axis=1)
        levelyears = levelpivot.swaplevel(0, 1, axis=1)
        levelcurrent= levelperiods[self.periods[self.period - 1]]
        
        #Get group info
        dfpivot = self.df[(self.df['cgroup'] == group) & (self.df['year'] == self.year)]
        test = pd.pivot_table(dfpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        groupperiods = test.swaplevel(0, 2, axis=1)
        groupyears = test.swaplevel(0, 1, axis=1) #Not used?
        currenteb = groupperiods[self.periods[self.period - 1]]
        
        currenttext =  "(" + group + ")" + self.cur[self.langg]
        prevtext = "(" + group + ")" + self.prev[self.langg]
        levellangtext = course + "(" + lang + ")"
        diagram = pd.DataFrame()
        diagram[currenttext] = currenteb[currenteb.keys()[-1]]
        diagram[levellangtext] = levelcurrent[currenteb.keys()[-1]]
        
        if self.period  not in  [1,6]:
            #Append previos eb infor for selected group  
            previouseb = groupperiods[self.periods[self.period - 2]]
            diagram[prevtext] = previouseb[previouseb.keys()[-1]]
            diagram=diagram[[prevtext,currenttext,levellangtext]]
            diagram = diagram.append(pd.DataFrame([(diagram[prevtext].mean(), diagram[currenttext].mean(), diagram[levellangtext].mean())], index=[self.avg[self.langg]], columns=[prevtext, currenttext, levellangtext]))
        else:
            diagram=diagram[[currenttext,levellangtext]]
            diagram = diagram.append(pd.DataFrame([(diagram[currenttext].mean(), diagram[levellangtext].mean())], index=[self.avg[self.langg]], columns=[currenttext, levellangtext]))
        
        self.generatePlot(diagram,func,group)

    def generateAllGroupPlots(self, func):
        """
        This function generates a plot for each group with the grades/pass% of each subject depending on func
        If the period is not the first, plots have a series with the previous period
        
        :param func: The function to use for aggregating grades, either np.mean or self.percent
        :return:
        """
        for group in self.df[self.df['year'] == self.year].cgroup.unique():
            if self.debug:
                print(self.year, group)
            self.generateGroupPlots(group,func)

    def generateGroupStatsPlots(self,group):
        pt = pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.period - 1])], index=["uniquename"], values=["grade"],
                            aggfunc=self.lowerThan).fillna('')
        if self.debug:
          print(pt)
        missed = self.notPassedStats(pt.grade)
        self.generatePiePlot(missed,group)
        #FIXME: Test if it works and delete
        #title = self.studpasstitle[self.langg]
        #title2 = self.promttitle[self.langg]
        #p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
        #if self.debug:
          #print(group+";"+str(sum(prom))+";"+str(sum(peligro)))
        #t = sum(p)
        #p = [x *100/ t for x in p]
        #legendpie = ("<=2","3-4","=>5")
        #colors = ['#6CA439', '#FF9C42', '#FF4848']
        #plt.suptitle(group, fontsize=14)
        #plt.subplot(1,2,1)
        #plt.bar(left,prom,color='#6CA439')
        #plt.bar(left,riesgo,color='#FF9C42')
        #plt.bar(left,peligro,color='#FF4848')
        #plt.title(title)
        #plt.xticks(np.array(left)+0.5, legendhist)
        #plt.subplot(1,2,2)
        #plt.pie(p,labels=legendpie,autopct='%1.1f%%',colors=colors)
        #plt.axis('equal')
        #plt.title(title2)
        #plt.savefig(self.workdir + "/" + group + "-" + self.periods[self.period-1] + "-" + self.langg + ".png")
        #plt.close()
        
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
            
    def generatePiedata(self,missed):
        '''
        :param missed: a list with the number of students for each number of not passed subjectcs
        :return p: a list with 3 values, number of students with <=2 not passed subjects, number of students with 3-4 not passed subjects, number of students with >=4 not passed subjects
        :return prom: a list with the number of students with 0-1-2 not passed subjects
        :return risk: a list with the number of students with 3-4 not passed subjects
        :return danger: a list with the number of students with 5-6... not passed subjects
        :return left: a list for with the x coordinates of the diagram bar
        :return legendhist: a list with the number of not passed subjects as legend for the diagram bar
        '''
        mmissed = np.max([int(k) for k in missed.keys()])
        if mmissed < 5: mmissed = 5
        prom=list([missed[0],missed[1],missed[2]])
        for k in range(3,mmissed+1):
            prom.append(0)
        risk = [0,0,0,missed[3],missed[4]]
        for k in range(5,mmissed+1):
            risk.append(0)
        danger=list()
        for k in range(5):
            danger.append(0)
        for k in range(5,mmissed+1):
            danger.append(missed[k])
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
        return p, prom, risk, danger, left, legendhist

    def generateAllStatsPlots(self,year=None,period=None):
        lang = 'eu'
        if not year: year = self.year
        if not period: period = self.periods[self.period - 1]
        pt = pd.pivot_table(self.df[(self.df.year == year) & (self.df.period == period)], index=["uniquename"], values=["grade"], aggfunc=self.lowerThan).fillna('')
        missed = self.notPassedStats(pt.grade)
        p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
        if self.debug:
           print(p,prom,riesgo,peligro, left,legendhist)

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
            for course in dflang[dflang.year == self.year].course.unique():
                if not lang: lang = "All"
                if self.debug:
                    print(course,lang)
                pt = pd.pivot_table(dflang[(dflang.course == course) & (dflang.year == self.year) & (
                dflang.period == self.periods[self.period - 1])], index=["uniquename"], values=["grade"],
                                  aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                print(course,lang,missed)
                self.generatePiePlot(missed,course+"-"+lang)
                #FIXME:Test and delete
                #title = self.studpasstitle[self.langg]
                #title2 = self.promttitle[self.langg]
                #p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
                #t = sum(p)
                #p = [x *100/ t for x in p]
                #legendpie = ("<=2","3-4","=>5")
                #colors = ['#6CA439', '#FF9C42', '#FF4848']
                #plt.suptitle(course + "-" + self.periods[self.period - 1], fontsize=14)
                #plt.subplot(1,2,1)
                #plt.bar(left,prom,color='#6CA439')
                #plt.bar(left,riesgo,color='#FF9C42')
                #plt.bar(left,peligro,color='#FF4848')
                #plt.title(title)
                #plt.xticks(np.array(left)+0.5, legendhist)
                #plt.subplot(1,2,2)
                #plt.pie(p,labels=legendpie,autopct='%1.1f%%',colors=colors)
                #plt.axis('equal')
                #plt.title(title2)
                #plt.savefig(self.workdir + "/" + course + "-" + lang + "-" + self.periods[self.period-1] + "-" + self.langg + ".png")
                #plt.close()
        return allg

    def generateCourseStatsEvolutionPlots(self,nyears=5,includelast=False):
        """
        This funcition generates a plot for each course: 0-2 not passed, 3-4 and 5 or more
        with the average stats of each period for the las 5 courses
        :return:creates a plot with the average stats of each period for the las 5 courses
        """
        #FIXME: Not only me, but save all pictures in a separate folder!
        allg = defaultdict(str)
        for lang in ['AG', 'D', None]:  # [df.lang.unique(),None]:
            if lang:
                dflang = self.df[self.df['lang'] == lang]
            else:
                dflang = self.df
            print(dflang[dflang.year == self.year].course.unique())
            for course in dflang[dflang.year == self.year].course.unique(): #FIXME: Using course it generates a nan course, but with coursename there are problems with and without lomce...
                if type(course)!=type('a'):
                    print("Break:",course, " - lang:", lang)
                    continue
                missedg = defaultdict(dict)
                if not lang: lang = "All"
                if self.debug:
                    print(course,lang)
                    
                datayp = []
                if includelast:
                    lastc = len(dflang.year.unique())
                else:
                    lastc = -1
                for y in sorted(dflang.year.unique())[-(nyears+1):lastc]: #FIXME: When a course finishes and there is no data for the next one, the report still generates stats without it
                    for p in dflang[dflang.year == y].period.unique():
                        if p == 'Ohiz kanpoko Ebaluazioa': #This is an special period,  only those with pending subjects after the Azkena do it. So skip it to the Final
                            continue
                        pt = pd.pivot_table(dflang[(dflang.course == course) & (dflang.year == y) & (dflang.period == p)], index=["uniquename"], values=["grade"], aggfunc=self.lowerThan).fillna('')
                        missed = self.notPassedStats(pt.grade)
                        _,prom,riesgo,peligro, _,_= self.generatePiedata(missed)
                        t = (sum(prom)+sum(riesgo)+sum(peligro))/100
                        dict1 = {}
                        dict1.update({'year':y,'period':p,'0-2': sum(prom)/t,'3-4': sum(riesgo)/t,'+5':sum(peligro)/t}) 
                        datayp.append(dict1)
                    
                data = pd.DataFrame(datayp, columns=['year','period','0-2','3-4','+5'])
                
                means = data.groupby('period').mean()
                errors = data.groupby('period').aggregate(np.std)
                
                styles1 = ['gs--','y^--','ro--']
                means.plot(yerr=errors,style=styles1)
                #means.plot(style=styles1)
                plt.ylim(0, 100)
                #plt.xticks(np.array(range(len(dflang.period.unique())))+0.5, dflang.period.unique())
                
                #FIXME: The generated plot doesn't have margins at both sides, It's ugly
                #I can't either keep the colors with the yerr
                
                plt.title("Course: "+ course + "(" + lang + ")")
                #plt.show()
                plt.savefig(self.workdir + "/" + course + "-" + lang + "-evolution-" + self.langg + ".png")
                plt.close()
        return allg


    def generateYearsAllGoodSubjects(self,period,percentaje=70,years=None):
        years=['2007-2008','2008-2009','2009-2010','2010-2011','2011-2012','2012-2013','2013-2014','2014-2015','2015-2016','2016-2017','2017-2018']
        good = []
        for year in years:
            passpercent = pd.pivot_table(self.df[(self.df['period']==period) & (self.df['year']==year)], index=["subject"], values=["grade"],margins=True,aggfunc=self.percent).fillna('')
            passpercent.columns = ["positivepercentage"]
            bad = passpercent[passpercent.positivepercentage<percentaje]
            pergood = 100-len(bad)*100/len(passpercent)
            good.append(pergood)
        return list(zip(years,good))

 

    def generatePassPercent(self,period,year,group = None,percentaje = 70):
        '''
        generates CSV files whit information about subjects and its passing %
        '''
        if group:
            framefilter = (self.df['period']==period) & (self.df['year']==year) & (self.df['cgroup']==group)
        else:
            framefilter = (self.df['period']==period) & (self.df['year']==year)
        passpercent = pd.pivot_table(self.df[framefilter], index=["subject"], values=["grade"],margins=True,aggfunc=self.percent).fillna('') #FIXME: Something more global subject is in basque
        passpercent.columns = ["positivepercentage"]
        bad = passpercent[passpercent.positivepercentage<percentaje]
        perbad = len(bad)*100/len(passpercent)
        if self.debug:
           print(str(group))#period," of ",year," Course")
           print("Subject with less than %" + str(percentaje) + " ap: %","{0:.2f}".format(perbad))
           pd.options.display.float_format = '{:,.2f}%'.format
           print(bad)
        #print("Group;" + str(group) +";"+ str(percentaje) + " ap: %;",str(100-perbad))
        print(group,";",perbad)
        import os.path
        fname = self.workdir+"/groupbadsubjs.csv"
        if not os.path.isfile(fname):
            with open(fname, 'w') as csvfile:
                    fieldnames = ['group', 'badsubjs']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
        with open(fname, 'a') as csvfile:
                    fieldnames = ['group', 'badsubjs']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({'group':group, 'badsubjs':perbad})
        passpercent.to_csv(self.workdir+"/ehunekoak-"+period+"-"+year+"-"+str(group)+".csv")
        bad.to_csv(self.workdir+"/ehunekoak-"+period+"-"+year+"-"+str(group)+"BAD.csv")


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
        pts = pd.pivot_table(self.df[self.df.year == self.year], rows=["course","subject"],values=["grade"],cols=["lang","period"],margins=True,aggfunc=np.mean).fillna('')
            #pts.ix['1. Batxilergoa LOE'].ix["Latina I"][0] AG 1. eb (bakarrik 1 eb)
            # n.subjectsavg["2015-2016"].ix['2. Batxilergoa LOE'].ix["Latina II"].grade.AG[0] 1. eb
        self.subjectsavg[year] = pts

    def generateStatsStudentPandas(self,year,ebal):
        students = self.df[self.df.year == self.year].uniquename.unique()#FIXME excludedCourses?
        print("<html><body>")
        for student in students:
            print("<h1>",student,"</h1>")
            pts = pd.pivot_table(self.df[(self.df.uniquename == student) & (self.df.year == self.year)], rows=["subject"],values=["grade"],cols=["period"],margins=True,aggfunc=np.mean).fillna('')
            print(pts.to_html(classes="table table-striped",float_format=lambda x: '%10.2f' % x))
        print("</body></html>")
            
    # Pendienteak kurtsoan bertan agertzen dira, 2. batx badu 1. batx pendiente course=2. batx
    def generateStatsAllStudents(self,mod=None, groups=None,doc=False):
        '''
        Generates a html file foreach group, which includes a table with each student marks (present and past periods)
        and also a graph with the same data plus a column with the average of the course
        '''
        ebals = self.periods[:self.period]
        legend = [e for e in ebals]
        legend.append("mailaren BB")
        groupsp = groups
        if not groups:
            courses = self.df[self.df.year == self.year].course.unique()#FIXME excludedCourses?
        else:
            g1 = self.generateORpandas("self.df.cgroup", groups)
            filter = "(self.df.year == self.year) & (self.df.period == self.period ) & " + g1
            courses = self.df[eval(filter)].course.unique()
        for course in sorted(courses):
            if self.debug:
                 print("course: ",course)
            self.generateStatsCourse(self.year,ebals,mod, course)
            groups = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.course == course)].cgroup.unique()
            if groupsp:
                groups = [g for g in groups if g in groupsp]
            for group in groups:
                if self.debug:
                   print("group: ",group)
                subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent = self.generateStatsGroup(group)
                sdf = self.df[["uniquename","fullname"]]
                sdf.drop_duplicates(inplace=True)
                #try to have student names not ids
                #print(sdf.head())
                #print(groupgrades.head())
                studentsnotpasses = pd.merge(studentsnotpasses,sdf,on="uniquename")
                cols = studentsnotpasses.columns.tolist() 
                cols = cols[-1:] + cols[1:-1]
                studentsnotpasses = studentsnotpasses[cols]
                
                students = self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1]) & (self.df.course == course) & (self.df.cgroup == group)].uniquename.unique()
                htmlmenu = ""
                ghtml = ""
                if doc:
                    doc = td.textdoc()
                    doc.addImageHeaderFooter(self.header,self.footer)
                    doc.addTitle(self.summary[self.langg] + " " + group)
                    doc.addTitle2(self.gresults[self.langg],True)
                    doc.addTitle3(self.promttitle[self.langg],False)
                    doc.addImage(self.workdir+pie,group+" promotion")
                    doc.addTitle3(self.average[self.langg])
                    doc.addImage(self.workdir+mean,group+" average grades")
                    doc.addTitle3(self.paspercent[self.langg])
                    doc.addImage(self.workdir+percent,group+" subjects pass percent")
                    doc.addTitle3(self.more70[self.langg])
                    if not badsubjectsgroup.empty:
                        bsg = badsubjectsgroup.set_index("name_" + self.langg,drop=True)#("name_"+self.langg+"",drop=True)
                        bsg.round({'%':2}) #does not work
                        doc.addTable(bsg.reset_index().values,["name_" + self.langg]+list(badsubjectsgroup.columns[1:]))
                    
                    #TODO askabi and group data
                    #in 1013 +/- self.td = self.getTutorsData()
                    self.td = self.getTutorsData() #FIXME it does not work if askabi's data is not present!
                    self.translation = {'group': {'eu': 'Taldea','es':'Grupo'},
               'harreman_ik': {'eu': 'Ikasleen arteko harremanak','es':'Relaciones entre el alumnado'},
               'harreman_ik_irak': {'eu': 'Ikasle eta irakasleen arteko harremanak','es':'Relaciones entre el alumnado y el profesorado'},
               'KonfHar': {'eu': 'Harremanen adostasuna','es':'Conformidad relaciones'},
               'materiala': {'eu': 'Materialaren zainketa','es':'Cuidado del material'},
               'garbitasuna': {'eu': 'Gelaren garbitasuna','es':'Limpieza del aula'},
               'KonfGar': {'eu': 'Gelaren adostasuna','es':'Conformidad aula'},
               'promoting': {'eu': 'Promozionatzen duten ikasleen %','es':'% de alumnado que promociona'},
               'Danger5': {'eu': '5 suspentso edo gehiago duen ikasleen %','es':'% alumnado con 5 suspensos o más'},
               'KonfProm': {'eu': 'Promozioaren adostasuna','es':'Conformidad promoción'},
               'badsubjs': {'eu': 'Gaindituen %70 baino gutxiago duten ikasgaien %','es':'% de asignaturas con menos de un 70% de aprobados'},
               'KonfIkasgai': {'eu': 'Ikasgaien gaindituen adostasuna','es':'Conformidad aprobado asignaturas'},
               'suspavg': {'eu': 'Ikasleen bataz besteko suspentso kopurua','es':'Promedio de suspensos por alumnos'},
               'bizikidetza_kopur': {'eu': 'Erregistratutako bizikidetza arazo kopurua','es':'Número de incidencias de convivencia registradas'},
               'part': {'eu' : 'Atala', 'es': 'Apartado' },
               'period': {'eu': 'Ebaluazioa','es':'Evaluación'},
               'EzKonforme': {'eu': 'Ez Ados','es':'No Conforme'},
               'Konforme': {'eu': 'Ados','es':'Conforme'}}
                    if self.td != '':
                        table = td.Table()
                        table.addElement(td.TableColumn(numbercolumnsrepeated=2))
                        headers=[self.translation['part'][self.langg],'2 ' + self.translation['period'][self.langg]]#,"2. Ebaluazioa","Azken Ebaluazioa"]
                        tr = td.TableRow()
                        table.addElement(tr)
                        for val in headers:
                            tc = td.TableCell(stylename="Table")
                            tr.addElement(tc)
                            p = td.P(stylename=doc.tableheaders,text=val)
                            tc.addElement(p)
                        import re #names in EDUCA and ASKABI are different
                        g = re.sub(r"[ \.º]", "", group)
                        g = re.sub(r'Bach2|Batx2', '6', g)
                        g = re.sub(r'Bach1|Batx1', '5', g)
                        print(g)
                    
                        f = self.td[g]
                        for line in f:
                            if "group" in line: #FIXME: If not all group tables contain a row with the group name (also in text header...)
                                continue
                            tr = td.TableRow()
                            table.addElement(tr)
                            for i,val in enumerate(line):
                                if i==0:
                                    tc = td.TableCell(stylename="Table")
                                    tr.addElement(tc)
                                    p = td.P(stylename=doc.tablecontents,text=self.translation[val][self.langg])
                                elif val=="EzKonforme":
                                    tc = td.TableCell(stylename="Table")
                                    tr.addElement(tc)
                                    p = td.P(stylename=doc.tablecontentscenterred,text=self.translation[val][self.langg])
                                elif val=="Konforme":
                                    tc = td.TableCell(stylename="Table")
                                    tr.addElement(tc)
                                    p = td.P(stylename=doc.tablecontentscenter,text=self.translation[val][self.langg])
                                else:
                                    tc = td.TableCell(stylename="Table")
                                    tr.addElement(tc)	   
                                    p = td.P(stylename=doc.tablecontentscenter,text=val)
                                tc.addElement(p)

                        doc.addTitle3(self.groupstats[self.langg],True)
                        doc.textdoc.text.addElement(table)
                    
                    #ENDTODO
                    
                    doc.addTitle2(self.sresults[self.langg],True)
                    doc.addTitle3(self.notpas[self.langg])
                    snp = studentsnotpasses.set_index("fullname",drop=True)
                    doc.addTable(snp.reset_index().values,["Student"]+list(studentsnotpasses.columns[1:]))
                else:
                    doc = False
                for studentid in sorted(students): #FIXME: This sorts by uniquename, better fullname
                    studentname = str(sdf[sdf.uniquename==studentid].fullname.item())
                    if self.debug:
                        print("student: ",studentid," name:" + studentname)
                    htmlmenu = htmlmenu + '<li><a href=\"#' + "-".join(str(studentid).split()) + '\">' + studentname + '</a></li>'
                    html = self.generateStatsStudent(studentid,studentname,groupgrades,doc)
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
                          </div></nav>
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
                if doc:
                    self.createDir(self.workdir + "/groups")
                    doc.save(self.workdir + "/groups/" + group + "_" + self.langg + ".odt")  #FIXME: os.path.join

    def generateStatsCourse(self, year, ebals, mod=None, course=None):
        if self.debug:
           print(course)#FIXME: subject find better, it is in basque
        coursegrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.course == course)],index=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        courseaverage = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.course == course)],index=["course"],values=["grade"],margins=True,aggfunc=np.mean).fillna(0)
        subjectscoursept = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.course == course)],index=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')
        badsubjectscourse = subjectscoursept[subjectscoursept.grade<70]
        badsubjectscourse.unstack()
        badsubjectscourse.reset_index(level=0,inplace=True)
        #Another way to calculate each course's subjects average
        #The average of all course is different with pandas or sql, does pandas calculate the avg of the avgs of each subject?
        subjectsavg = {}
        subjects = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.course == course)].subject.unique()
        for subject in subjects:
            subjectsavg[subject] = str(coursegrades.ix[subject].grade)
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        avg = cur.execute("SELECT AVG(grade) FROM grades WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchone()#FIXME to pandas
        con.close()
        subjectsavg["BB"] = str(avg[0])
        if self.debug:
           print("AVG: ",subjectscoursept,badsubjectscourse,coursegrades,courseaverage,subjectsavg)

    def generateStatsGroup(self, group, diagrams=True):
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
        if self.debug:
           print(group)
        lang = self.df[(self.df.year == self.year) & (self.df.cgroup == group)].lang.unique()[0]
        if self.debug:
           print("Eredua: ",lang)
        students = self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1]) & (self.df.cgroup == group)].uniquename.unique()
        groupgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1])  & (self.df.cgroup == group)],index=["name_" + self.langg],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        groupgrades.unstack()
        groupgrades.reset_index(level=0, inplace=True)
        subjectsgrouppt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1])  & (self.df.cgroup == group)],index=["name_" + self.langg],values=["grade"],margins=True,aggfunc=self.percent).fillna('')#this one could return percentajes of all subjects, not only bad ones!
        badsubjectsgroup = subjectsgrouppt[subjectsgrouppt.grade<70] #FIXME: 70 hardcoded
        badsubjectsgroup.unstack()
        badsubjectsgroup.reset_index(level=0,inplace=True)
        badsubjectsgroup.columns=["name_" + self.langg,"%"]
        studentsnotpasses = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1])  & (self.df.cgroup == group)],index=["uniquename"],values=["grade"],aggfunc=[self.lowerThan,np.mean]).fillna('')
        studentsnotpasses.unstack()
        studentsnotpasses.reset_index(level=0,inplace=True)
        studentsnotpasses.columns=["uniquename","<5","avg"]
        studentsnotpasses.sort_values(by='<5',ascending=[0],inplace=True)      
        #self.generateGroupStatsPlots()#year, ebal, group=group)
        #pie = str(group) + "/" + year + "-" + ebal + str(group) + ".png"
        pie = str(group) + "-" + self.periods[self.period-1] + "-" + self.langg + ".png"
        mean = str(group) + ' - ' + self.periods[self.period - 1] + " (" + self.year + ") " + "-mean-" + self.langg + ".png"
        percent = str(group) + ' - ' + self.periods[self.period - 1] + " (" + self.year + ") " + "-percent-" + self.langg + ".png"
        if diagrams:
            self.generateGroupPlots(group, np.mean) #For all plots, pass year and ebal. Or should they be global? optional argument..
            self.generateGroupPlots(group, self.percent)
            self.generateGroupStatsPlots(group)
        return subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent

    def generateStatsStudent(self,student,fullname,groupgrades,doc=False):
        '''
        generates html with a table for the students with subjects and his marks side by side with all group marks
        studentgroupgrades is a DataFrame with those marks
        
        TODO:change subject with "name_"+self.langg
        
        :param student: uniquename of the student
        :param fullname: The name of the studetns to use as title for the diagrams and filename
        :param groupgrades: the grades of the group of the student to create a comparative diagram
        :param doc: a textdoc() object to append the report of the student (default False)
        :return html: html code with the report of the student (grades)
        '''
        #FIXME: subject is in basque
        if self.debug:
           print(student)
        studentgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1]) & (self.df.uniquename == student)],index=["name_" + self.langg],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        studentgrades.unstack()
        studentgrades.reset_index(level=0, inplace=True)
        studentgroupgrades = pd.merge(studentgrades,groupgrades,on="name_" + self.langg)
        studentgroupgrades.columns = ["name_" + self.langg, student,'course']
        dfs = self.df[["name_" + self.langg,"abv_"+self.langg]]
        dfs.drop_duplicates(subset="name_" + self.langg,keep='last',inplace=True)
        studentgroupgrades = pd.merge(studentgroupgrades,dfs,on="name_" + self.langg)#FIXME: I'm trying to have the abreviations in the plot and text in the table. IF it works abv_es has to be considered
        studentgroupgrades.drop("name_" + self.langg, axis=1, inplace=True)
        studentgroupgrades.columns = [fullname,'course',"name_" + self.langg]
        studentgroupgrades = studentgroupgrades[["name_" + self.langg,fullname,'course']]
        
        if self.debug:
           print(studentgroupgrades)
        group = self.df[(self.df.uniquename==student)&(self.df.year==self.year)].cgroup.unique()[0]#FIXME: I don't like looking up the group this way, but I don't like to pass to much paramters either
        self.createDir(self.workdir + group)
        fname = group + "/" + self.year + "-" + self.periods[self.period-1] + "-" + student + ".png" #to use self.workdir + group + "/" + we need to create group dir first self.createDir(self.workdir + group)
        plt.clf()
        studentgroupgrades.plot(kind="bar",x=studentgroupgrades["name_" + self.langg])
        plt.ylim(0, 10)
        plt.axhline(5)
        plt.savefig(self.workdir + fname, format="png")
        plt.close()
        if doc:
            doc.addTitle3(fullname,True)
            studentgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == self.periods[self.period-1]) & (self.df.uniquename == student)],index=["name_"+self.langg+""],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
            studentgrades.unstack()
            studentgrades.reset_index(level=0, inplace=True)
                        
            studentgradesdoc = studentgrades.set_index("name_"+self.langg,drop=True)
            doc.addTable(studentgradesdoc.reset_index().values,["name_"+self.langg]+list(studentgradesdoc.columns))
            doc.addImage(self.workdir+fname,fullname+" grades")
        html = '''
        <div class="student">
            <h1 style=\"clear: both;\" id='%s'></h1>
            <h1> %s  <a href=#top>(top)</a></h1>
            <div class="row" style=\"display: flex; align-items: center;\">
            <div class="col-md-3 col-sm-6">
            %s
            </div>
        <div class="col-md-7 col-sm-6">
        <img class="img-responsive center-block"  style=\"float: left; margin: 0px 0px 15px 15px;vertical-align: middle;\" src=\"%s\">
        </div>
        </div>
        </div>'''%("-".join(str(student).split()),fullname,studentgrades.to_html(index=False,classes="table table-striped",float_format=lambda x: '%10.2f' % x),fname)
        return html
    
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
        courses = self.df[self.df.year == self.year].course.unique()#FIXME excludedCourses?
        with open(self.workdir+"/groupstats.csv", 'a') as csvfile:
                    fieldnames = ['group', 'total',"promoting","risk34","Danger5","notpassedtot","suspavg"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
        for course in courses:
            groups = self.df[(self.df.year == self.year) & (self.df.course == course)].cgroup.unique()
            groupsd={}
            groupsc=[] #FIXME: Change group name to adapt to askabi's naming
            for group in groups:
                group1 = group.replace(". ", "")
                group1 = group1.replace("º ", "")
                groupsd[group1]=group
                groupsc.append(group1)
            groupsc.sort()
            #remove "º "  and ". "
            groupslist=[]
            for group in groupsc:
                pt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == period) & (self.df.cgroup == groupsd[group])], index=["uniquename"], values=["grade"], aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                p, prom, riesgo, peligro, left, legendhist = self.generatePiedata(missed)
                a=prom[0],sum(prom[1:]),sum(riesgo),sum(peligro)#prom has only 3 values 0 susp, 1susp and 2 susp, others are 0
                t=sum(a)
                a = [x *100/ t for x in a]
                groupslist.append(a)
                notpassed = 0
                for key, value in missed.items():
                    notpassed += key*value
                print(group,";",t,";",p[0],";",p[2],";",notpassed,";",notpassed/t)
                with open(self.workdir+"/groupstats.csv", 'a') as csvfile:
                    fieldnames = ['group', 'total',"promoting","risk34","Danger5","notpassedtot","suspavg"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({'group':group, 'total':t,"promoting":p[0],"risk34":p[1],"Danger5":p[2],"notpassedtot":notpassed,"suspavg":notpassed/t})

            df=pd.DataFrame(groupslist)
            df.columns=l
            df=df.transpose()
            df.columns=groupsc
            df=df.transpose()
            barcolors = ['#6CA439', '#3074AE','orange', 'red']
            df.plot(kind='bar', stacked=True,title=course,color=barcolors,)
            plt.ylim(0, 100)
            plt.legend( loc=8, ncol=4, mode="expand", borderaxespad=0.)
            plt.savefig(self.workdir+"/"+course + '-allgroupsprom.png')
            plt.close()
            
    def mergegroupstatsaskabi(self,askfile=None):
        
        #FIXME: In the report i use promoting as percentaje, here it is as absolute.
        #Either change here calculating the percentaje or change the csv genration
        #and konfprom function
        
        def konf5(row,cols):
            print(row,cols)
            print(row[cols[0]],type(row[cols[0]]))
            print(row[cols[1]],type(row[cols[1]]))
            if float(row[cols[0]])+float(row[cols[1]]) >= 10:
                return "Konforme"
            else:
                return "EzKonforme"
        
        def konfprom(row):
            if (row["promoting"]>=60) & (row["Danger5"]<20):
                return "Konforme"
            else:
                return "EzKonforme"
        
        def konfikas(row):
            if self.debug == True:
                print(row['badsubjs'],row['badsubjs']<40)
            if row['badsubjs']<40:
                return "Konforme"
            else:
                return "EzKonforme"
            
        def topercent(row,col):
            return float(row[col])*100/int(row['total'])
        
        gst = pd.read_csv(self.workdir+"/groupstats.csv")
        gst.replace({'\.{1}': '','º':'',' ':''}, regex=True,inplace=True) #names in EDUCA and ASKABI are different
        gst.replace({'Bach2': '6','Batx2':'6','Bach1': '5','Batx1':'5'}, regex=True,inplace=True)
        gst["Danger5"] = gst.apply (lambda row: topercent(row,'Danger5'),axis=1)
        gst["promoting"] = gst.apply (lambda row: topercent(row,'promoting'),axis=1)
        gst["KonfProm"] = gst.apply (lambda row: konfprom(row),axis=1)
        
        gbs = pd.read_csv(self.workdir+"/groupbadsubjs.csv")
        gbs.replace({'\.{1}': '','º':'',' ':''}, regex=True,inplace=True)
        gbs.replace({'Bach2': '6','Batx2':'6','Bach1': '5','Batx1':'5'}, regex=True,inplace=True)
        gbs["KonfIkasgai"] = gbs.apply (lambda row: konfikas(row),axis=1)
        
        if askfile:
            ad = pd.read_csv(askfile)
        else:
            ad = pd.read_csv(self.workdir+"/tutore.csv",encoding="ISO-8859-15")
        columns_drop = ['urtea','data','zenbat?','giroa','analisia','koordina_zerbitzu', 'balorazioa','oso_ongi', 'hobekutza']
        ad.drop(columns_drop, axis=1, inplace=True)
        ad.drop('docent', axis=1, inplace=True) #FIXME: Etorkizuenean gorde beharko zen
        ad.drop('tut_erregistroa', axis=1, inplace=True) #FIXME: Etorkizuenean gorde beharko zen
        ad["KonfHar"] = ad.apply (lambda row: konf5(row,["harreman_ik","harreman_ik_irak"]),axis=1)
        ad["KonfGar"] = ad.apply (lambda row: konf5(row,["garbitasuna","materiala"]),axis=1)
        
        allg =  pd.merge(gst,gbs,right_on="group",left_on="group")
        alld = pd.merge(allg,ad,how="left",right_on="taldea",left_on="group")
        
        
        #['harreman1', 'harreman2', 'KonfHar', 'material','garbitasun', 'KonfGar', 'Promozionatzen', 'suspasko', 'KonfProm','Suspikasgai', 'KonfIkasgai', 'Suspikasle','Bizikidetza']
        zutabeak = ['group','harreman_ik','harreman_ik_irak', 'KonfHar', 'materiala','garbitasuna', 'KonfGar','promoting','Danger5', 'KonfProm','badsubjs', 'KonfIkasgai', 'suspavg','bizikidetza_kopur','risk34','total','eba']
        alld = alld.reindex(columns=zutabeak)
        alld.sort_values('group',inplace=True)
        alld.fillna('',inplace=True)
        alld.to_csv(self.workdir+"/reportgruoupdata.csv")
                
        return alld
    
    def getTutorsData(self):
        df = pd.read_csv(self.workdir+"/reportgruoupdata.csv",sep=",")
        taldeak = df.group.unique()
        zutabeak = ['id','group','harreman_ik','harreman_ik_irak', 'KonfHar', 'materiala','garbitasuna', 'KonfGar','promoting','Danger5', 'KonfProm','badsubjs', 'KonfIkasgai', 'suspavg','bizikidetza_kopur','risk34','total','eba']
        columns_drop = ['risk34','total','eba']
        df.drop(columns_drop, axis=1, inplace=True)
        df.fillna('',inplace=True)
        tdata = {}
        for t in taldeak:
            dfn = df[df.group==t]
            l=[]
            for column in dfn:
                a=dfn[column].tolist()
                a.insert(0,column)
                l.append(a)
            tdata[t] = l[1:]
        return tdata
    
if __name__ == "__main__":
    #db = "/home/asier/Hezkuntza/SGCC/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluacion/Python-educa/mendillorri.db"
    db = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/mendillorriN.db"
    ebaluaketak = ['1. Ebaluazioa', '2. Ebaluazioa', '3. Ebaluazioa', 'Azken Ebaluazioa', 'Ohiz kanpoko Ebaluazioa','Final']
    ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA",'Programa de Currículo Adaptado LOMCE']
    divpmar=["3º Div.Cur.","4º Div. Cur.","3º PMAR"]
    batx=["1. Batxilergoa LOE","2. Batxilergoa LOE"]
    dbh=["2. DBH","1. DBH","3. DBH","4. DBH"]
    baliogabekokurtsoak = ucepca
    #files = ["/home/asier/Hezkuntza/SGCC-Erregistroak-15-16/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluación/1º Ev/Sabanas 2º Bach 27-11/1ev-2bach.csv"]
    #n.insertdataDB(files)
    year = "2017-2018"
    for lang in ['eu','es']:
      n = notak(db,lang)
      n.setWorkDir("ebaluaketa1718")
      n.getData(year, ebaluaketak, 2, baliogabekokurtsoak)
      n.generateFinalGrade()
      n.generateYearsAllGoodSubjects(ebaluaketak[1])
      #n.removepending()
      #print("course np.mean")
      #n.generateCoursePlots(np.mean)
      #print("course percent")
      #n.generateCoursePlots(n.percent)
      #n.promcourseplots("1. Ebaluazioa")
      #taldeak = n.df[n.df.year == year].cgroup.unique()
      #for t in taldeak:
        #n.generateGroupStatsPlots(t)
      #n.generateAllGroupStatsPlots()
      #taldeak = n.df[n.df.year == year].cgroup.unique()
      #for t in taldeak:
        #n.generatePassPercent("1. Ebaluazioa",year,t)
      #n.generateAllGroupPlots(np.mean)
      #n.generateAllGroupPlots(n.percent)
      #n.generateCoursePlots(np.mean)
      #n.generateCoursePlots(n.percent)
    n.generateCourseStatsEvolutionPlots()
    #n.generateCourseStatsPlots()
    #print("generate All Stats Plots")
    #n.generateAllStatsPlots()
    #print("generate Stats Student")
    #n.generateStatsAllStudents(doc=True)
    #n.generatePrymarySchoolPlots(np.mean)
    #n.generateDeptPlots([np.mean,n.percent])
    

##Create report for schools. Add in selector lang (D-AG) and then compute for all and each school...    
#import pandas as pd
#pd.pivot_table(n.df[(n.df.course == "1 ESO") & (n.df.year == n.year) & (n.df.period == n.periods[0])], index=["uniquename","primaryschool","lang"], values=["grade"],columns=["subject"]).fillna('')
#s=pd.pivot_table(n.df[(n.df.course == "1 ESO") & (n.df.year == "2012-2013") & (n.df.period == n.periods[5])], index=["uniquename","primaryschool","lang"], values=["grade"],columns=["subject"]).fillna('')    
##more data:
#select names.fullname,yeardata.uniquename,yeardata.lang,yeardata.repeating from yeardata,names where year="2015-2016" and  yeardata.course="1. DBH LOMCE" and names.primaryschool="CPEIP Pam. Mendillorri" and names.uniquename=yeardata.uniquename order by names.uniquename

#import notakeb as notak
#db = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/mendillorriN.db"
#ebaluaketak = ['1. Ebaluazioa', '2. Ebaluazioa', '3. Ebaluazioa', 'Azken Ebaluazioa', 'Ohiz kanpoko Ebaluazioa','Final']
#ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA",'Programa de Currículo Adaptado LOMCE']
#divpmar=["3º Div.Cur.","4º Div. Cur.","3º PMAR"]
#batx=["1. Batxilergoa LOE","2. Batxilergoa LOE"]
#dbh=["2. DBH","1. DBH","3. DBH","4. DBH"]
#baliogabekokurtsoak = ucepca
#year = "2016-2017"
#for lang in ['eu','es']:
    #n = notak.notak(db,lang)
    #n.setWorkDir("2. Ebaluazioa2016-2017")
    #n.getData(year, ebaluaketak, 2, baliogabekokurtsoak)
    #n.generateCourseBilvsCooursePlots(n.percent)


#import notakeb as notak
#db = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/mendillorriN.db"
#ebaluaketak = ['1. Ebaluazioa', '2. Ebaluazioa', '3. Ebaluazioa', 'Azken Ebaluazioa', 'Ohiz kanpoko Ebaluazioa','Final']
#ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA",'Programa de Currículo Adaptado LOMCE']
#divpmar=["3º Div.Cur.","4º Div. Cur.","3º PMAR"]
#batx=["1. Batxilergoa LOE","2. Batxilergoa LOE"]
#dbh=["2. DBH","1. DBH","3. DBH","4. DBH"]
#baliogabekokurtsoak = ucepca
#year = "2017-2018"
#lang = 'es'
#n = notak.notak(db,lang)
#n.setWorkDir("test")
#n.getData(year, ebaluaketak, 6, baliogabekokurtsoak)
#n.generateCourseStatsEvolutionPlots()
#g = re.sub(r"[ \.º]", "", group)
#g = re.sub(r'Bach2|Batx2', '6', g)
#g = re.sub(r'Bach1|Batx1', '5', g)
#print(g)
