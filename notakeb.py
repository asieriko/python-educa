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
rcParams.update({'figure.autolayout': True}) #TODO it makes small plots with very big labels, I've to figure how to change subject names with abreviations
# in each? plt.gca().tight_layout()


class notak:


    barcolors = ['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3']
    #piecolors = ['#6CA439', '#FF9C42', '#FF4848']
    plt.rc('axes', facecolor='#FFFEEE', edgecolor='#4E3629')
    plt.rc('patch', facecolor='#6CA439', edgecolor='#517B2B', linewidth=0)
    plt.rc('figure', figsize=(16,6))
    plt.rc('font', size=14.0)
    plt.rc('axes', prop_cycle=(cycler('color',['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3'])))
    plt.rc('lines', linewidth=4)    

    def __init__(self, db, lang='es'):
        """
        Initiates the class
        :param db: the sqlite3 db file path
        :return: None
        """
        self.db = db
        self.debug = False
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
        html = ""


    def configure(self, year, periods, unekoeb=1, excludedCourses=[], debug=False):
        """
        Configures course and group ploting
        :param year: The year whose marks will be plotted
        :param periods: Evaluative period list
        :param unekoeb: Current period as int (as index+1 for the list)
        :param excludedCourses: Courses that won't generate a plot
        :param baliogabekolaburdurak: Abreviations that won't generate a plot
        :return:
        """
        self.debug=debug
        self.year = year
        self.periods = periods
        #self.excludedCourses = [str(ec.decode()) for ec in excludedCourses]
        self.excludedCourses =  excludedCourses
        notcourses = "NOT grades.course = '" + ("' AND NOT grades.course = '").join(
            excludedCourses) + "'"  # The query works if excludedCourses = []
        self.ebnumber = unekoeb
        if self.ebnumber > len(self.periods):#FIXME: raise ValueError
            print("Error: ebnumber > eb kopurua")
        ebselect = "grades.period = '" + ("' OR grades.period = '").join(
            self.periods[:self.ebnumber]) + "'"
        con = sqlite3.connect(self.db)
        sql="SELECT yeardata.year, yeardata.course AS coursename, yeardata.cgroup, yeardata.lang,\
            yeardata.uniquename, names.fullname, \
            grades.subject, grades.code, grades.period, grades.grade \
        FROM \
            yeardata,grades,names \
        WHERE \
            yeardata.year=grades.year AND yeardata.uniquename=grades.uniquename \
            AND yeardata.uniquename=names.uniquename \
            AND yeardata.course=grades.course \
            AND NOT (grades.grade='') AND (" + notcourses + ") \
            AND (" + ebselect + ") AND grades.course!='2016-2017'"
        if self.debug:
           print(sql)
        self.df = pd.read_sql(sql,con)
        sqlsubjects = "SELECT * FROM abreviations"
        dfsubjects = pd.read_sql(sqlsubjects,con)
        dfsubjects.drop_duplicates(subset='code',keep='last',inplace=True)
        con.close()
        self.df = pd.merge(self.df,dfsubjects,on="code",how="left")#FIXME: Somethin more global would be right
        if self.debug:
           print(self.df.head())
        #self.df.drop(['id', 'name'], inplace=True, axis=1)
        self.df.grade = self.df.grade.astype(int)
        if self.debug:
           print(self.df.head())
        self.df['bil'] = self.df['lang'].map(self.modeloBil)
        self.df['lang'] = self.df['lang'].map(self.modelo)

    def generateFinalGrade(self):
        '''
        This function geneates new rows with the final grade for each year-studet-subject
        This final grade is the las ordinary one if passed or the extraordinary one.
        '''
        grouped = self.df[(self.df.period=="Ohiz kanpoko Ebaluazioa")|(self.df.period=="Azken Ebaluazioa")].groupby(['year','uniquename','subject'])
        newrows = grouped.apply(self.finalgrade)
        self.df = pd.concat([self.df,newrows])
        self.df.reset_index(drop=True,inplace=True)
        return newrows #Not needed

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
        :return:
        """
        self.dfp = df[df.coursename!=df.ycourse]

    def removepending(self):
        """
        Removes pending subjects from the dataframe
        :return:
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
        Calculates the % of >=5 marks (from 10) in a list x
        :param x: list with grades (0-10)
        :return:
        """
        return sum(1 for a in x if a >= n) * 100 / len(x) if len(x) != 0 else ''

    def lowerThan(self,x,n=5):
        '''
        Calculates the amount of values in x that are less than n
        :param x: list with grades (0-10)
        :return:
        '''
        return sum(1 for a in x if a < n)

    def modelo(self, x):
        """
        :param x:list with course language
        :return:D for D and AG for A or G
        """
        if x == 'D':
            return 'D'
        elif x in ['A','G','G-A.Eleb.In.','A-A.Eleb.In.']:
            return 'AG'

    def modeloBil(self, x):
        """
        :param x:list with course language
        :return:D for D and AG for A or G
        """
        if x == 'D':
            return 'D'
        elif x in ['A','G']:
            return 'AG'
        elif x in ['G-A.Eleb.In.','A-A.Eleb.In.']:
            return 'AGbil'

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

    def generatesheet(self, group):
        """
        Generates a table with the grades for each student and subject
        for the configured year and period
        Only for current year and eb'
        :param group: Name of the group
        """
        return pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.ebnumber - 1])], index=["uniquename"], values=["grade"],
                              columns=["subject"]).fillna('')


    def notPassedStats(self,dfgrades):
        """
        From a list returns a dic with the number of not passed subjects and students
        :param dfgrades: a grades series with names as index 
            niquename
            aabadiacaj     0
            aalvardiaz     0
            acarvalper     8
            agarciacha     0
            ajimenemen2    0
            aruedasbal     2
            ausandilor     0
            ...
        :return: gradescount a dic with the number of not passed subjects and student number
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

    def getdata(self,group):
        '''
        Generates stats about failures in the specified group, for the configured year and period
        [66.66666666666667, 13.333333333333334, 20.0], 2.2666666666666666
        :param group: name of the group
        :return: p - a list with the percent of students in each situation (promoting <= 2 susp, risk 3-4 susp, danger > 4 susp) and the average of fails for students
        '''
        pt = pd.pivot_table(self.df[(self.df.cgroup == group) & (self.df.year == self.year) & (
        self.df.period == self.periods[self.ebnumber - 1])], index=["uniquename"], values=["grade"],
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
            p,m=self.getdata(group)  
        return df

    def generatePlot(self,diagram,func,coursegroup):
        '''
        Generates a bar plot from the diagram dataframe
        :param diagram: Dataframe with the data to be ploted
        :param func: it can be the average of the grades (mean) or the percentaje of passed for each subject
        :param coursegroup: only needed to create the filename
        :return: None, it stores the plot in the filesystem
        '''
        gtitle = coursegroup + " (" + self.year + ") " + self.periods[self.ebnumber - 1]
        
        #print(coursegroup)
        #print(diagram)
        #print(len(list(diagram.index)))
        #barcolors = ['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3']
        #left = np.arange(len(list(diagram.index)))  # the x locations for the groups
        #width = 0.27 
        #for i in range(len(diagram.columns)):
            #plt.bar(left+width*i,list(diagram.ix[:,i]),width,color=barcolors[i],label=diagram.columns[i])
        #plt.xticks(np.array(left)+0.5, list(diagram.index))
        #plt.xticks(rotation=90)
        #plt.legend(loc='center left')
        
        # diagram.plot(kind='bar',title=gtitle).legend(loc='center left', bbox_to_anchor=(1,0.5))
        diagram.plot(kind='bar', title=gtitle).legend(loc=4) #FIXME: Original, but changed in order to have fancier colors issue with pandas 0.17
        plt.title(gtitle)
        # plt.show()
        if func.__name__ == 'mean':
            plt.ylim(0, 10)
            plt.axhline(5)
        else:
            plt.ylim(0, 100)
            plt.axhline(70)
        figurefile = gtitle + '-' + func.__name__ + '-'+self.langg+'.png'
        plt.savefig(self.workdir+"/"+figurefile)
        plt.close()
   
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
                if course in self.excludedCourses:
                    continue
                if self.debug:
                   print(self.year, course)
                coursedf = dflang[dflang['course'] == course]
                courseyearebspivot = pd.pivot_table(coursedf, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot =courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                selectperiods = courseyearebspivot.swaplevel(0, 2, axis=1)
                selectyears = courseyearebspivot.swaplevel(0, 1, axis=1)
                currenteb = selectperiods[self.periods[self.ebnumber - 1]]
                
                years = coursedf.year.unique()
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
                if self.ebnumber != 1:
                    previouseb = selectperiods[self.periods[self.ebnumber - 2]]
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
        dfyearscourses = self.df[self.df.bil=="AGbil"][["course","year"]].drop_duplicates()
        dfcourses = n.df[(n.df.bil=="AGbil")&(n.df.year==n.year)][["course","year"]].drop_duplicates()
        for lang in ['AG', 'D', None]:  # [df.lang.unique(),None]:
            if lang:
                dflang = self.df[self.df['lang'] == lang]
            else:
                dflang = self.df
                lang='All'
            for course in dflang[dflang.year == self.year].course.unique():#FIXME: Change in other functions coursename for course. Coursename has LOMCE, course not
                if course in self.excludedCourses:
                    continue
                if self.debug:
                   print(self.year, course)
                coursedf = dflang[dflang['course'] == course]
                courseyearebspivot = pd.pivot_table(coursedf, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"],aggfunc=func)
                #Remove subjects that are not in the current period/course
                courseyearebspivot =courseyearebspivot[courseyearebspivot[courseyearebspivot.columns[len(courseyearebspivot.columns)-1]].notnull()]
                selectperiods = courseyearebspivot.swaplevel(0, 2, axis=1)
                selectyears = courseyearebspivot.swaplevel(0, 1, axis=1)
                currenteb = selectperiods[self.periods[self.ebnumber - 1]]
                
                years = coursedf.year.unique()
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
                if self.ebnumber != 1:
                    previouseb = selectperiods[self.periods[self.ebnumber - 2]]
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

    def generatePrymarySchoolPlots(self, func):
        pass


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
        course = self.df[(self.df.year == self.year) & (self.df.cgroup == group)].coursename.unique()[0]
        if self.debug:
           print("Eredua: ",lang)
        levelpivot = self.df[(self.df['lang'] == lang) & (self.df['year'] == self.year) & (self.df['coursename'] == course)]
        levelpivot = pd.pivot_table(levelpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        levelperiods = levelpivot.swaplevel(0, 2, axis=1)
        levelyears = levelpivot.swaplevel(0, 1, axis=1)
        levelcurrent= levelperiods[self.periods[self.ebnumber - 1]]
        
        #Get group info
        dfpivot = self.df[(self.df['cgroup'] == group) & (self.df['year'] == self.year)]
        test = pd.pivot_table(dfpivot, index=["abv_"+self.langg+""], values=["grade"], columns=['year', "period"], aggfunc=func)
        groupperiods = test.swaplevel(0, 2, axis=1)
        groupyears = test.swaplevel(0, 1, axis=1) #Not used?
        currenteb = groupperiods[self.periods[self.ebnumber - 1]]
        
        currenttext =  "(" + group + ")" + self.cur[self.langg]
        prevtext = "(" + group + ")" + self.prev[self.langg]
        levellangtext = course + "(" + lang + ")"
        diagram = pd.DataFrame()
        diagram[currenttext] = currenteb[currenteb.keys()[-1]]
        diagram[levellangtext] = levelcurrent[currenteb.keys()[-1]]
        
        if self.ebnumber != 1:
            #Append previos eb infor for selected group  
            previouseb = groupperiods[self.periods[self.ebnumber - 2]]
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
        self.df.period == self.periods[self.ebnumber - 1])], index=["uniquename"], values=["grade"],
                            aggfunc=self.lowerThan).fillna('')
        if self.debug:
          print(pt)
        missed = self.notPassedStats(pt.grade)
        title = self.studpasstitle[self.langg]
        title2 = self.promttitle[self.langg]
        p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
        if self.debug:
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
            
    def generatePiedata(self,missed):
        '''
        :param missed:
        :param coursegroup:
        :param lang:
        :return :
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
        if not period: period = self.periods[self.ebnumber - 1]
        pt = pd.pivot_table(self.df[(self.df.year == year) & (self.df.period == period)], index=["uniquename"], values=["grade"], aggfunc=self.lowerThan).fillna('')
        missed = self.notPassedStats(pt.grade)
        p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
        if self.debug:
           print(self.generatePiedata(missed))

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
                if self.debug:
                    print(course,lang)
                pt = pd.pivot_table(dflang[(dflang.coursename == course) & (dflang.year == self.year) & (
                dflang.period == self.periods[self.ebnumber - 1])], index=["uniquename"], values=["grade"],
                                  aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                title = self.studpasstitle[self.langg]
                title2 = self.promttitle[self.langg]
                p,prom,riesgo,peligro, left,legendhist = self.generatePiedata(missed)
                t = sum(p)
                p = [x *100/ t for x in p]
                legendpie = ("<=2","3-4","=>5")
                colors = ['#6CA439', '#FF9C42', '#FF4848']
                plt.suptitle(course + "-" + self.periods[self.ebnumber - 1], fontsize=14)
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
        years=['2007-2008','2008-2009','2009-2010','2010-2011','2011-2012','2012-2013','2013-2014','2014-2015','2015-2016']
        good = []
        for year in years:
            eh = pd.pivot_table(self.df[(self.df['period']==period) & (self.df['year']==year)], index=["subject"], values=["grade"],margins=True,aggfunc=n.percent).fillna('')
            eh.columns = ["positivepercentage"]
            bad = eh[eh.positivepercentage<percentaje]
            pergood = 100-len(bad)*100/len(eh)
            good.append(pergood)
        return list(zip(years,good))

    def generatePassPercent(self,period,year,group = None,percentaje = 70):
        '''
        generates CSV files whit information about subjects and its passin %
        '''
        if group:
            framefilter = (self.df['period']==period) & (self.df['year']==year) & (self.df['cgroup']==group)
        else:
            framefilter = (self.df['period']==period) & (self.df['year']==year)
        eh = pd.pivot_table(self.df[framefilter], index=["subject"], values=["grade"],margins=True,aggfunc=self.percent).fillna('') #FIXME: Something more global subject is in basque
        eh.columns = ["positivepercentage"]
        bad = eh[eh.positivepercentage<percentaje]
        perbad = len(bad)*100/len(eh)
        if self.debug:
           print(str(group))#period," of ",year," Course")
           print("Subject with less than %" + str(percentaje) + " ap: %","{0:.2f}".format(perbad))
           pd.options.display.float_format = '{:,.2f}%'.format
           print(bad)
        #print("Group;" + str(group) +";"+ str(percentaje) + " ap: %;",str(100-perbad))
        eh.to_csv(self.workdir+"/ehunekoak-"+period+"-"+year+"-"+str(group)+".csv")
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
        pts = pd.pivot_table(self.df[self.df.year == self.year], rows=["coursename","subject"],values=["grade"],cols=["lang","period"],margins=True,aggfunc=np.mean).fillna('')
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
            if self.debug:
                 print("course: ",course)
            self.generateStatsCourse(year,ebals,mod, course)
            groups = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].cgroup.unique()
            if groupsp:
                groups = [g for g in groups if g in groupsp]
            for group in groups:
                if self.debug:
                   print("group: ",group)
                subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent = self.generateStatsGroup(year, ebal, ebals, group)
                sdf = self.df[["uniquename","fullname"]]
                sdf.drop_duplicates(inplace=True)
                #try to have student names not ids
                groupgrades = pd.merge(groupgrades,sdf,on="uniquename")
                print(groupgrades.head())
                
                students = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course) & (self.df.cgroup == group)].uniquename.unique()
                htmlmenu = ""
                ghtml = ""
                for studentid in sorted(students):
                    studentname = str(sdf[sdf.uniquename==studentid].fullname.item())
                    if self.debug:
                        print("student: ",studentid," name:" + studentname)
                    htmlmenu = htmlmenu + '<li><a href=\"#' + "-".join(str(studentid).split()) + '\">' + studentname + '</a></li>'
                    html = self.generateStatsStudent2(year,ebal,ebals,studentid,studentname,groupgrades)
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

    def generateStatsCourse(self, year, ebals, mod=None, course=None):
        if self.debug:
           print(course)#FIXME: subject find better, it is in basque
        coursegrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],index=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        courseaverage = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],index=["coursename"],values=["grade"],margins=True,aggfunc=np.mean).fillna(0)
        subjectscoursept = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)],index=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')
        badsubjectscourse = subjectscoursept[subjectscoursept.grade<70]
        badsubjectscourse.unstack()
        badsubjectscourse.reset_index(level=0,inplace=True)
        #Another way to calculate each course's subjects average
        #The average of all course is different with pandas or sql, does pandas calculate the avg of the avgs of each subject?
        subjectsavg = {}
        subjects = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.coursename == course)].subject.unique()
        for subject in subjects:
            subjectsavg[subject] = str(coursegrades.ix[subject].grade)
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        avg = cur.execute("SELECT AVG(grade) FROM grades WHERE year=? AND period=? AND course=?", [year, ebals[-1], course]).fetchone()#FIXME to pandas
        con.close()
        subjectsavg["BB"] = str(avg[0])
        if self.debug:
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
        if self.debug:
           print(group)
        lang = self.df[(self.df.year == year) & (self.df.cgroup == group)].lang.unique()[0]
        if self.debug:
           print("Eredua: ",lang)
        students = self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.cgroup == group)].uniquename.unique()
        groupgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],index=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        groupgrades.unstack()
        groupgrades.reset_index(level=0, inplace=True)
        subjectsgrouppt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],index=["subject"],values=["grade"],margins=True,aggfunc=self.percent).fillna('')#this one could return percentajes of all subjects, not only bad ones!
        badsubjectsgroup = subjectsgrouppt[subjectsgrouppt.grade<70] #FIXME: 70 hardcoded
        badsubjectsgroup.unstack()
        badsubjectsgroup.reset_index(level=0,inplace=True)
        badsubjectsgroup.columns=["subject","%"]
        studentsnotpasses = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1])  & (self.df.cgroup == group)],index=["uniquename"],values=["grade"],aggfunc=[self.lowerThan,np.mean]).fillna('')
        studentsnotpasses.unstack()
        studentsnotpasses.reset_index(level=0,inplace=True)
        studentsnotpasses.columns=["uniquename","<5","avg"]
        studentsnotpasses.sort_values(by='<5',ascending=[0],inplace=True)      
        #self.generateGroupStatsPlots()#year, ebal, group=group)
        #pie = str(group) + "/" + year + "-" + ebal + str(group) + ".png"
        pie = str(group) + "-" + ebal + "-" + self.langg + ".png"
        mean = str(group) + " (" + self.year +") " + ebal + "-mean-" + self.langg + ".png"
        percent = str(group) + " (" + self.year +") " + ebal + "-percent-" + self.langg + ".png"
        if diagrams:
            self.generateGroupPlots(group, np.mean) #For all plots, pass year and ebal. Or should they be global? optional argument..
            self.generateGroupPlots(group, self.percent)
            self.generateGroupStatsPlots(group)
        return subjectsgrouppt,badsubjectsgroup,groupgrades,studentsnotpasses,pie,mean,percent

    def generateStatsStudent2(self,year,ebal,ebals,student,fullname,groupgrades):
        '''
        generates html with a table for the students with subjects and his marks side by side with all group marks
        studentgroupgrades is a DataFrame with those marks
        '''
        #FIXME: subject is in basque
        if self.debug:
           print(student)
        studentgrades = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == ebals[-1]) & (self.df.uniquename == student)],index=["subject"],values=["grade"],margins=True,aggfunc=np.mean).fillna('')
        studentgrades.unstack()
        studentgrades.reset_index(level=0, inplace=True)
        studentgroupgrades = pd.merge(studentgrades,groupgrades,on="subject")
        studentgroupgrades.columns = ['subject', student,'course']
        dfs = self.df[["subject","abv_"+self.langg]]
        dfs.drop_duplicates(subset='subject',keep='last',inplace=True)
        studentgroupgrades = pd.merge(studentgroupgrades,dfs,on="subject")#FIXME: I'm trying to have the abreviations in the plot and text in the table. IF it works abv_es has to be considered
        studentgroupgrades.drop('subject', axis=1, inplace=True)
        studentgroupgrades.columns = [fullname,'course','subject']
        studentgroupgrades = studentgroupgrades[['subject',fullname,'course']]
        
        if self.debug:
           print(studentgroupgrades)
        group = self.df[(self.df.uniquename==student)&(self.df.year==year)].cgroup.unique()[0]#FIXME: I don't like looking up the group this way, but I don't like to pass to much paramters either
        self.createDir(self.workdir + group)
        fname = group + "/" + year + "-" + ebal + "-" + student + ".png" #to use self.workdir + group + "/" + we need to create group dir first self.createDir(self.workdir + group)
        plt.clf()
        studentgroupgrades.plot(kind="bar",x=studentgroupgrades.subject)
        plt.ylim(0, 10)
        plt.axhline(5)
        plt.savefig(self.workdir + fname, format="png")
        plt.close()
        html = ""
        html = html + '''
        <div class="student">
            <h1 style=\"clear: both;\" id='%s'></h1>
            <h1> %s  <a href=#top>(top)</a></h1>
            <div class="row" style=\"display: flex; align-items: center;\">
            <div class="col-md-3 col-sm-6">'''%("-".join(str(student).split()),fullname)
        html = html + studentgrades.to_html(index=False,classes="table table-striped",float_format=lambda x: '%10.2f' % x) + '''</div>
        <div class="col-md-7 col-sm-6">
        <img class="img-responsive center-block"  style=\"float: left; margin: 0px 0px 15px 15px;vertical-align: middle;\" src=\"%s\">
        </div>
        </div>
        </div>'''%(fname)
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
                pt = pd.pivot_table(self.df[(self.df.year == self.year) & (self.df.period == period) & (self.df.cgroup == groupsd[group])], index=["uniquename"], values=["grade"], aggfunc=self.lowerThan).fillna('')
                missed = self.notPassedStats(pt.grade)
                p, prom, riesgo, peligro, left, legendhist = self.generatePiedata(missed)
                a=prom[0],sum(prom[1:]),sum(riesgo),sum(peligro)#prom has only 3 values 0 susp, 1susp and 2 susp, others are 0
                t=sum(a)
                a = [x *100/ t for x in a]
                groupslist.append(a)
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
    
if __name__ == "__main__":
    #db = "/home/asier/Hezkuntza/SGCC/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluacion/Python-educa/mendillorri.db"
    db = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/mendillorriN.db"
    ebaluaketak = ['1. Ebaluazioa', '2. Ebaluazioa', '3. Ebaluazioa', 'Azken Ebaluazioa', 'Ohiz kanpoko Ebaluazioa','Final']
    ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA"]
    divpmar=["3º Div.Cur.","4º Div. Cur.","3º PMAR"]
    batx=["1. Batxilergoa LOE","2. Batxilergoa LOE"]
    dbh=["2. DBH","1. DBH","3. DBH","4. DBH"]
    baliogabekokurtsoak = ucepca
    #files = ["/home/asier/Hezkuntza/SGCC-Erregistroak-15-16/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluación/1º Ev/Sabanas 2º Bach 27-11/1ev-2bach.csv"]
    #n.insertdataDB(files)
    year = "2016-2017"
    for lang in ['eu','es']:
      n = notak(db,lang)
      n.setWorkDir("1ebaluaketa16-17")
      n.configure(year, ebaluaketak, 1, baliogabekokurtsoak)
      #n.removepending()
      print("course np.mean")
      n.generateCoursePlots(np.mean)
      print("course percent")
      n.generateCoursePlots(n.percent)
      n.promcourseplots("1. Ebaluazioa")
      taldeak = n.df[n.df.year == year].cgroup.unique()
      for t in taldeak:
        n.generateGroupStatsPlots(t)
      n.generateAllGroupStatsPlots()
      taldeak = n.df[n.df.year == year].cgroup.unique()
      for t in taldeak:
        n.generatePassPercent("1. Ebaluazioa",year,t)
      n.generateAllGroupPlots(np.mean)
      n.generateAllGroupPlots(n.percent)
      n.generateCoursePlots(np.mean)
      n.generateCoursePlots(n.percent)
    
    n.generateCourseStatsPlots()
    print("generate All Stats Plots")
    n.generateAllStatsPlots()
    print("generate STats Student")
    n.generateStatsStudent("2016-2017", "1. Ebaluazioa")#,groups=("Bach.2A","Bach.2B","Batx.2H","Batx.2I","Batx.2J"))

#import notakeb
#import numpy as np
#n = notakeb.notak("mendillorriN.db","eu")
#n.setWorkDir("1ebaluaketa15-16")
#n.configure("2015-2016", ["1. Ebaluazioa"], 1)
#n.df = n.df[n.df.year!="2016-2017"]
##n.generateCoursePlots(np.mean)
##n.promcourseplots("1. Ebaluazioa")
##n.generateAllGroupPlots(np.mean)
#taldeak = n.df[n.df.year == "2015-2016"].cgroup.unique()
#for t in taldeak:
    #n.generateGroupStatsPlots(t)
#n.generateAllGroupStatsPlots()
#taldeak = n.df[n.df.year == "2015-2016"].cgroup.unique()
#for t in taldeak:
    #n.generatePassPercent("Azken Ebaluazioa","2015-2016",t)
#n.generateStatsStudent("2015-2016","1. Ebaluazioa")