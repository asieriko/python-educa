import pandas as pd
import numpy as np
import unittest
from pandas.util.testing import assert_frame_equal

import notakeb

class KnownValues(unittest.TestCase):          


    def test_notPassedStats(self):    
        n = notakeb.notak("mendillorriN.db","eu")
        n.setWorkDir("1ebaluaketa15-16")
        n.configure("2015-2016", ["1. Ebaluazioa"], 1)
        n.df = n.df[n.df.year!="2016-2017"]
        
        s = pd.Series([0,0,8,0,0,2,0,2,2,0,3,1,1,1,0,8,8,3,1,1,0,2,2,5,5,0,0,4,6,3], index=["aabadiacaj","aalvardiaz","acarvalper","agarciacha","ajimenemen2","aruedasbal","ausandilor","cmoralegil","dlopezarra","dmoreirpad","etamarerod","gmorenogob","gperezgarc","icabodeder","iiribarjul","imatillbla","jarminogal","jcarazoval","jcorrei1","jotazubosq","myaguancab","nurrutipla","pgayarrarr1","psamperdel","psantamlar1","rsaizherre","tdiallo","vcunhasori","wameziaaho","zcastrogar"])
        s.name="grade"
        s.index.name="uniquename"
        result = n.notPassedStats(s)
        expected = {0: 10, 1: 5, 2: 5, 3: 3, 4: 1, 5: 2, 6: 1, 8: 3}
        self.assertDictEqual(result,expected)
        
        
    def test_generatePiedata(self):
        n = notakeb.notak("mendillorriN.db","eu")
        n.setWorkDir("1ebaluaketa15-16")
        n.configure("2015-2016", ["1. Ebaluazioa"], 1)
        n.df = n.df[n.df.year!="2016-2017"]
        missed = {0: 10, 1: 5, 2: 5, 3: 3, 4: 1, 5: 2, 6: 1, 7: 0, 8: 3}
        result = (n.generatePiedata(missed))
        expected = ([20, 4, 6],[10, 5, 5, 0, 0, 0, 0, 0, 0],[0, 0, 0, 3, 1, 0, 0, 0, 0],[0, 0, 0, 0, 0, 2, 1, 0, 3],[0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],['0', '1', '2', '3', '4', '5', '6', '7', '8'])
        self.assertEqual(result,expected)
        
    def test_getdata(self):    
        n = notakeb.notak("mendillorriN.db","eu")
        n.setWorkDir("1ebaluaketa15-16")
        n.configure("2015-2016", ["1. Ebaluazioa"], 1)
        n.df = n.df[n.df.year!="2016-2017"]
        data = {'cgroup':['1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A'],
        'year':['2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016'],
        'period':['1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa'],
        'uniquename':['aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2'],
        'grade':[7,8,6,9,8,8,6,6,7,6,7,8,8,7,7,7,8,7,7,6,3,5,3,4,3,4,4,5,4,4,8,8,8,5,8,7,6,7,7,7,7,7,6,8,8,6,6,9,6,9]}
        n.df = pd.DataFrame(data)
        result = (n.getdata("1º A"))
        expected = ([80.0, 0.0, 20.0], 1.6)
        self.assertEqual(result,expected)
        
    def test_generateStatsGroup(self):
        n = notakeb.notak("mendillorriN.db","eu")
        n.setWorkDir("1ebaluaketa15-16")
        n.configure("2015-2016", ["1. Ebaluazioa"], 1)
        n.df = n.df[n.df.year!="2016-2017"]
        data = {'cgroup':['1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A','1º A'],
        'year':['2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016','2015-2016'],
        'lang':['AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG','AG'],
        'period':['1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa','1. Ebaluazioa'],
        'subject':['mate','gazte','ing','mus','tek','plas','giz','biogeo','fran','eusk','mate','gazte','ing','mus','tek','plas','giz','biogeo','fran','eusk','mate','gazte','ing','mus','tek','plas','giz','biogeo','fran','eusk','mate','gazte','ing','mus','tek','plas','giz','biogeo','fran','eusk','mate','gazte','ing','mus','tek','plas','giz','biogeo','fran','eusk'],
        'uniquename':['aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aabadiacaj','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','aalvardiaz','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','acarvalper','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','agarciacha','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2','ajimenemen2'],
        'grade':[3,8,6,9,8,8,6,6,7,6,3,8,8,7,7,7,8,7,7,6,3,5,3,4,3,4,4,5,4,4,3,8,8,5,8,7,6,7,7,7,7,7,6,8,8,6,6,9,6,9]}
        n.df = pd.DataFrame(data)
        rsubjectsgrouppt,rbadsubjectsgroup,rgroupgrades,rstudentsnotpasses,rpie,rmean,rpercent = (n.generateStatsGroup("2015-2016",n.periods[n.ebnumber-1],n.periods,"1º A", False))
        data = {'subject':['biogeo','eusk','fran','gazte','giz','ing','mate','mus','plas','tek','All'],
        'grade':['100.0','80.0','80.0','100.0','80.0','80.0','20.0','80.0','80.0','80.0','78.0']}
        esubjectsgrouppt = pd.DataFrame(data)
        esubjectsgrouppt.set_index("subject",inplace=True)
        esubjectsgrouppt['grade'] = esubjectsgrouppt.grade.astype(float)
        data = {'subject':['mate'],
        '%':['20.0']}
        ebadsubjectsgroup = pd.DataFrame(data)
        ebadsubjectsgroup = ebadsubjectsgroup[["subject","%"]]
        ebadsubjectsgroup['%'] = ebadsubjectsgroup['%'].astype(float)
        data = {'subject':['biogeo','eusk','fran','gazte','giz','ing','mate','mus','plas','tek','All'],
        'grade':['6.8','6.4','6.2','7.2','6.0','6.2','3.8','6.6','6.4','6.8','6.24']}
        egroupgrades = pd.DataFrame(data)
        egroupgrades = egroupgrades[["subject","grade"]]
        egroupgrades['grade'] = egroupgrades.grade.astype(float)
        data = {'uniquename':['acarvalper','aabadiacaj','aalvardiaz','agarciacha','ajimenemen2'],
        '<5':[8,1,1,1,0],
        'avg':['3.9','6.7','6.8','6.6','7.2']}
        index = [2,0,1,3,4]
        estudentsnotpasses = pd.DataFrame(data,index=index)
        estudentsnotpasses['avg'] = estudentsnotpasses.avg.astype(float)
        estudentsnotpasses = estudentsnotpasses[["uniquename","<5","avg"]]
        epie = '1º A-1. Ebaluazioa-eu.png'
        emean = '1º A (2015-2016) 1. Ebaluazioa-mean-eu.png'
        epercent = '1º A (2015-2016) 1. Ebaluazioa-percent-eu.png'
        expected = ([80.0, 0.0, 20.0], 1.6)
        self.assertEqual(rpie,epie)
        self.assertEqual(rmean,emean)
        self.assertEqual(rpercent,epercent)
        assert_frame_equal(rsubjectsgrouppt,esubjectsgrouppt)
        assert_frame_equal(rbadsubjectsgroup,ebadsubjectsgroup)
        assert_frame_equal(rgroupgrades,egroupgrades)
        assert_frame_equal(rstudentsnotpasses,estudentsnotpasses)
        
        
if __name__ == '__main__':
    unittest.main()        