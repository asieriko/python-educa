import getpass
import numpy as np
import notakeb as notak
import database as db
import getEducaData as ged

if __name__=="__main__":
    dbfile = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/mendillorriN.db"
    data = db.database(dbfile)
    year = "2016-2017"
    y = input("Year ["+year+"]:")
    if y != '':
        year = y
    ud = input("Update data y/N: ")
    if ud in ['y','Y']:
        print("updating data")
        user = input("username: ")
        passwd = getpass.getpass()
        try:
            getdata = ged.GetEDUCAdata(user,passwd,verbose=False)
            getdata.getallcurrentgrades()
            data.delete_last_years_grades(year)
            data.insert_grades(["/home/asier/Hezkuntza/python-hezkuntza/python-educa/data/grades"+year+".csv"])
        except:
            print("An error ocurred")
            raise
    ebaluaketak = ['1. Ebaluazioa', '2. Ebaluazioa', '3. Ebaluazioa', 'Azken Ebaluazioa', 'Ohiz kanpoko Ebaluazioa','Final']
    print("Hautatu ebaluaketa")
    for i,eb in enumerate(ebaluaketak):
        print("\t",i+1,": ",eb)
    eb = len(ebaluaketak)
    while eb not in list(range(len(ebaluaketak))):
        eb = int(input("Sartu eb zenbakia: "))-1
    ucepca=["4. C.E.U.","3. C.E.U","2. C.E.U.","1. Oinarrizko Hezkuntza (C.E.U.)","Programa de Currículo Adaptado","PCA","Programa de Currículo Adaptado LOMCE"]
    baliogabekokurtsoak = ucepca
    for lang in ['eu','es']:
        n = notak.notak(dbfile,lang)
        n.setWorkDir(ebaluaketak[eb]+year)
        if ebaluaketak[eb] == 'Final':
            n.generateFinalGrade()
        n.getData(year, ebaluaketak, eb+1, baliogabekokurtsoak)

        print("course np.mean")
        n.generateCoursePlots(np.mean)
        print("course percent")
        n.generateCoursePlots(n.percent)
        taldeak = n.df[n.df.year == year].cgroup.unique()
        print("Group stats plots")
        for t in taldeak:
            n.generateGroupStatsPlots(t)
        print("All group stats plots")
        n.generateAllGroupStatsPlots()
        taldeak = n.df[n.df.year == year].cgroup.unique()
        print("Group pass percent")
        for t in taldeak:
            n.generatePassPercent(ebaluaketak[eb],year,t)
        print("All group plots np.mean")
        n.generateAllGroupPlots(np.mean)
        print("All group plots n.percent")
        n.generateAllGroupPlots(n.percent)
    
    
    print("course prom plots")
    n.promcourseplots(ebaluaketak[eb])
    print("Departaments plots")
    n.generateDeptPlots([np.mean,n.percent])
    print("Primary School plots")
    n.generatePrymarySchoolPlots(np.mean)
    print("Bilingual plots")
    n.generateCourseBilvsCooursePlots(np.mean)
    print("Course stats plots")
    n.generateCourseStatsPlots()
    print("generate All Stats Plots")
    n.generateAllStatsPlots()
    print("generate Stats Student")
    n.generateStatsAllStudents(doc=True)
    
    print("Mix askabi and EDUCA for the report")
    n.mergegroupstatsaskabi()
