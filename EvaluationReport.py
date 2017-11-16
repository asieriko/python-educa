'''
This script creates an odt document with a summary of the evaluation data
In needs a OrderedDict with the courses, languages and groups for each one of them
It also needs the plots of each course, lang, group. Both subjects and promotion
And it needs too a csv file with a summary of each group data (cleaning, care, ...) 
'''

from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, GraphicProperties, TableCellProperties
from odf.style import PageLayout, MasterPage, Header, Footer
from odf.text import P, H, List, ListItem
from odf.draw  import Page, Frame, TextBox, Image
from odf.table import Table, TableColumn, TableRow, TableCell
import csv
import pandas as pd
from collections import OrderedDict

textdoc = OpenDocumentText()
#pl = PageLayout(name="pagelayout")
#textdoc.automaticstyles.addElement(pl)
#mp = MasterPage(name="Standard", pagelayoutname=pl)
#textdoc.masterstyles.addElement(mp)
#h = Header()
#hp = P(text="2. ebaluazioko txostena")
#h.addElement(hp)
#mp.addElement(h)


# Create a style for the paragraph with page-break
withbreak = Style(name="WithBreak", parentstylename="Standard", family="paragraph")
withbreak.addElement(ParagraphProperties(breakbefore="page"))
textdoc.automaticstyles.addElement(withbreak)

h1style = Style(name="Heading 1",  family="paragraph",parentstylename="Heading 1")
h1style.addElement(GraphicProperties(fill="solid",fillcolor="#e6e6ff"))
h1style.addElement(TextProperties(attributes={'fontsize':"14pt",'fontweight':"bold",'color':"#000099" }))
h1style.addElement(ParagraphProperties(breakbefore="page",margintop="0.4cm",marginbottom="0.2cm",backgroundcolor="#e6e6ff",padding="0.05cm",borderleft="none",borderright="none",bordertop="none",borderbottom="2.01pt solid #000099",shadow="none"))
textdoc.automaticstyles.addElement(h1style)

h2style = Style(name="Heading 2", family="paragraph",parentstylename="Heading 2")
h2style.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold",'color':"#000099" }))
h2style.addElement(ParagraphProperties(breakbefore="page",marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
textdoc.automaticstyles.addElement(h2style)

h3style = Style(name="Heading 3", family="paragraph",parentstylename="Heading 3")
h3style.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold",'color':"#000099" }))
h3style.addElement(ParagraphProperties(breakbefore="page",marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
textdoc.automaticstyles.addElement(h3style)

TAB_style = Style(name="Table", family="table-cell", parentstylename="Standard")
TAB_style.addElement(TableCellProperties(border="0.05pt solid #000000"))
textdoc.automaticstyles.addElement(TAB_style)

TAB_stylered = Style(name="Table red", family="table-cell", parentstylename="Standard")
TAB_stylered.addElement(TableCellProperties(backgroundcolor="ff0000",border="0.05pt solid #000000"))
textdoc.automaticstyles.addElement(TAB_stylered)

tableheaders = Style(name="Table Headers", family="paragraph", parentstylename="Standard")
tableheaders.addElement(ParagraphProperties(numberlines="false", linenumber="0",textalign="center",margintop="0.2cm",marginbottom="0.2cm"))
tableheaders.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold"}))
textdoc.styles.addElement(tableheaders)

tablecontents = Style(name="Table Contents", family="paragraph", parentstylename="Standard")
tablecontents.addElement(ParagraphProperties(numberlines="false", linenumber="0",margintop="0.2cm",marginbottom="0.2cm"))
tablecontents.addElement(TextProperties(attributes={'fontsize':"12pt" }))
textdoc.styles.addElement(tablecontents)

tablecontentscenter = Style(name="Table Contents Center", family="paragraph", parentstylename="Standard")
tablecontentscenter.addElement(ParagraphProperties(numberlines="false", linenumber="0", textalign="center",margintop="0.2cm",marginbottom="0.2cm"))
tablecontentscenter.addElement(TextProperties(attributes={'fontsize':"12pt" }))
textdoc.styles.addElement(tablecontentscenter)

tablecontentscenterred = Style(name="Table Contents Center Red", family="paragraph", parentstylename="Standard")
tablecontentscenterred.addElement(ParagraphProperties(numberlines="false", linenumber="0", textalign="center", backgroundcolor="#ff0000",margintop="0.2cm",marginbottom="0.2cm"))
tablecontentscenterred.addElement(TextProperties(attributes={'fontsize':"12pt" }))
textdoc.styles.addElement(tablecontentscenterred)

lang="eu"
year="2017-2018"
period="1. Ebaluazioa"
path = "/home/asier/Hezkuntza/python-hezkuntza/python-educa/"+period+year+"/"
pie = "-" + period + "-" + lang + ".png"
mean = ' - ' + period + " (" + year + ") " + "-mean-" + lang + ".png"
percent = ' - ' + period + " (" + year + ") " + "-percent-" + lang + ".png"



translation = {'group': {'eu': 'Taldea','es':'Grupo'},
               'harreman_ik': {'eu': 'Ikasleen arteko harremanak','es':'Relaciones entre el alumnado'},
               'harreman_ik_irak': {'eu': 'Ikasle eta irakasleen arteko harremanak','es':'Relaciones entre el alumnado y el profesorado'},
               'KonfHar': {'eu': 'Harremanen adostasuna','es':'Conformidad relaciones'},
               'materiala': {'eu': 'Materialaren zainketa','es':'Cuidado del material'},
               'garbitasuna': {'eu': 'Gelaren garbitasuna','es':'Limpieza del aula'},
               'KonfGar': {'eu': 'Gelaren adostasuna','es':'Conformidad aula'},
               'promoting': {'eu': 'Promozionatzen duten ikasleen %','es':'% de alumando que promociona'},
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

#pl = PageLayout(name="pagelayout")
#textdoc.automaticstyles.addElement(pl)

#mp = MasterPage(name="Standard", pagelayoutname=pl)
#textdoc.masterstyles.addElement(mp)
#h = Header()
#img_path = "/home/asier/Hezkuntza/SGCC/PR04 Gestion documental/Plantillas - Logos - Encabezados/membrete.png"
#href = textdoc.addPicture(img_path)
#img = Image(href=href, type="simple", show="embed", actuate="onLoad")
#h.addElement(img)
#mp.addElement(h)


title = H(stylename=h1style,text="Taldeen adostasun maila",outlinelevel=1)
textdoc.text.addElement(title)

def groupPage(group,lang):
  grouptitle = H(stylename=h3style,text=group,outlinelevel=3)
  textdoc.text.addElement(grouptitle)
  blankline = P(text="")
  textdoc.text.addElement(blankline)
  
  if td != '':
    table = Table()
    table.addElement(TableColumn(numbercolumnsrepeated=2))
    headers=[translation['part'][lang],'2 ' + translation['period'][lang]]#,"2. Ebaluazioa","Azken Ebaluazioa"]
    tr = TableRow()
    table.addElement(tr)
    for val in headers:
        tc = TableCell(stylename="Table")
        tr.addElement(tc)
        p = P(stylename=tableheaders,text=val)
        tc.addElement(p)
    #f = [["garbitasuna",3,6],["materiala",6,8],["Adostasuna", "Ez konforme","konforme"],["Harremanak1",7,8],["Harremanak2",6,7],["Adostasuna", "konforme","konforme"]]
    f = td[group]
    for line in f:
        if "group" in line: #FIXME: If not all group tables contain a row with the group name (also in text header...)
            continue
        tr = TableRow()
        table.addElement(tr)
        for i,val in enumerate(line):
            if i==0:
                tc = TableCell(stylename="Table")
                tr.addElement(tc)
                p = P(stylename=tablecontents,text=translation[val][lang])
            elif val=="EzKonforme":
                tc = TableCell(stylename="Table")
                tr.addElement(tc)
                p = P(stylename=tablecontentscenterred,text=translation[val][lang])
            elif val=="Konforme":
                tc = TableCell(stylename="Table")
                tr.addElement(tc)
                p = P(stylename=tablecontentscenter,text=translation[val][lang])
            else:
                tc = TableCell(stylename="Table")
                tr.addElement(tc)	   
                p = P(stylename=tablecontentscenter,text=val)
            tc.addElement(p)

    textdoc.text.addElement(table)
    
    blankline = P(text="")
    textdoc.text.addElement(blankline)
  if lang=="eu":
    subjectsp = P(text="%70 baino gainditu gutxiago duten ikasgaiak:")
  else:
    subjectsp = P(text="Asignaturas con menos del %70 de aprobados:")
  textdoc.text.addElement(subjectsp)
  blankline = P(text="")
  textdoc.text.addElement(blankline)
  textList = List(stylename="L1")
  
  
  file = path+"ehunekoak-"+period+"-"+year+"-"+group+".csv"
  with open(file, 'r', encoding="UTF-8") as results:
     reader = csv.reader(results)
     headers = next(reader, None)  # get first row with headers
     for row in reader:
       if float(row[1]) < 70 and row[0]!= "All":
         item = ListItem()
         if lang=="eu":
            item.addElement(P(text=row[0]+": "+"{:.2f}".format(float(row[1])) +"%"))
         else:
            item.addElement(P(text=ikasgai[row[0]]+": "+"{:.2f}".format(float(row[1])) +"%"))
         textList.addElement(item)
         textdoc.text.addElement(textList)
     
  
  breakpage = P(stylename=withbreak,text="")
  textdoc.text.addElement(breakpage)
  
  for diagramtype in [pie,percent]:#,name2]:
    p = P()
    textdoc.text.addElement(p)
    img_path = path + group + diagramtype
    href = textdoc.addPicture(img_path)
    f = Frame(name=group+diagramtype, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
    p.addElement(f)
    img = Image(href=href, type="simple", show="embed", actuate="onLoad")
    f.addElement(img)
   
   
def coursePage(coursename,data,lang):
  coursetitle = H(stylename=h2style,text=coursename,outlinelevel=2)
  textdoc.text.addElement(coursetitle)
  blankline = P(text="")
  textdoc.text.addElement(blankline)    
  
  for diagramtype in [pie,percent]:
    p = P()
    textdoc.text.addElement(p)
    img_path = path + coursename + "-All" + diagramtype
    href = textdoc.addPicture(img_path)
    f = Frame(name=coursename+diagramtype, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
    p.addElement(f)
    img = Image(href=href, type="simple", show="embed", actuate="onLoad")
    f.addElement(img)

  for courselang in ['AG','D']:#data.keys():
     coursetitle = H(stylename=h2style,text=coursename+"-"+courselang,outlinelevel=2)
     textdoc.text.addElement(coursetitle)
     blankline = P(text="")
     textdoc.text.addElement(blankline)   
     
     for diagramtype in [pie,percent]:
       p = P()
       textdoc.text.addElement(p)
       img_path = path + coursename + "-" + courselang + diagramtype
       href = textdoc.addPicture(img_path)
       f = Frame(name=coursename+diagramtype+courselang, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
       p.addElement(f)
       img = Image(href=href, type="simple", show="embed", actuate="onLoad")
       f.addElement(img)
     
     for group in data[courselang]:
       groupPage(group,lang)

def ikasgaiak():
    ikasgai = {}
    with open("ikasgaiakitzulita.csv", 'r', encoding="UTF-8") as results:
     reader = csv.reader(results, delimiter=";")
     for row in reader:
       ikasgai[row[0]] = row[1]
    return ikasgai

  
def tutors():
  df = pd.read_csv(path + "reportgruoupdata.csv",sep=",")
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


ikasgai=ikasgaiak()
td = ''
td=tutors()  


#print(td["3º A"])

#coursegroups = OrderedDict({ '1 ESO': {'AG':['1A','1B', '1C','1D'], 'D':['1H', '1I',  '1J','1L']}, 
                 #'2º PMAR': {'AG':['2P'],'D':['2P']},           
                 #'2 ESO': {'AG':['2A','2B', '2C','2D'], 'D':['2H', '2I',  '2J']},
                 #'3 ESO': {'AG':['3A','3B','3C'], 'D':['3H','3I','3J','3K']},
                 #'4 ESO': {'AG':['4A','4B','4C','4D'], 'D':['4H', '4I', '4J','4K','4L']},
                 #'3º PMAR': {'AG':['3D'], 'D':['3L']},
                 #'1º Bach.': {'AG':['5A','5B'], 'D':[ '5H', '5I', '5J']},
                 #'2º Bach.': {'AG':['6A','6B'], 'D':['6H', '6I',  '6J']}
                 #})



coursegroups = OrderedDict({ '1 ESO': {'AG':['1º A','1º B', '1º C','1º D','1º E'], 'D':['1.H', '1.I',  '1.J','1. K','1.L']}, 
                 '2º PMAR': {'AG':['2º P'],'D':['2º P']},           
                 '2 ESO': {'AG':['2º A','2º B', '2º C','2º D'], 'D':['2.H', '2.I',  '2.J','2. K']},
                 '3 ESO': {'AG':['3º A','3º B','3º C'], 'D':['3.H','3.I','3.J']},
                 '4 ESO': {'AG':['4º A','4º B','4º C'], 'D':['4.H', '4.I',  '4.J','4.K']},
                 '3º PMAR': {'AG':['3º D'], 'D':['3.D']},
                 '1º Bach.': {'AG':['Bach.1A','Bach.1B'], 'D':[ 'Batx.1H', 'Batx.1I', 'Batx.1J']},
                 '2º Bach.': {'AG':['Bach.2A','Bach.2B'], 'D':['Batx.2H', 'Batx.2I',  'Batx.2J']}
                 })

courses = ['1 ESO','2 ESO','2º PMAR','3 ESO','3º PMAR','4 ESO','1º Bach.','2º Bach.']



for k in courses:
  coursePage(k,coursegroups[k],lang)
  
  
textdoc.save("report-"+period+year+"-"+lang+".odt")  

#coursegroups = OrderedDict({ '1. DBH LOMCE': {'AG':['1º A','1º B', '1º C','1º D'], 'D':['1.H', '1.I',  '1.J','1.L']}, 
                 #'2. DBH LOMCE': {'AG':['2º A','2º B', '2º C','2º D'], 'D':['2.H', '2.I',  '2.J']},
                 #'3. DBH LOMCE': {'AG':['3º A','3º B','3º C'], 'D':['3.H','3.I','3.J','3.K']},
                 #'4. DBH LOMCE': {'AG':['4º A','4º B','4º C','4º D'], 'D':['4.H', '4.I',  '4.J','4.K','4.L']},
                 #'3º PMAR': {'AG':['3º D'], 'D':['3.L']},
                 #'1. Batxilergoa LOE': {'AG':['Bach.1A','Bach.1B'], 'D':[ 'Batx.1H', 'Batx.1I', 'Batx.1J']},
                 #'2. Batxilergoa LOE': {'AG':['Bach.2A','Bach.2B'], 'D':['Batx.2H', 'Batx.2I',  'Batx.2J']}
                 #})

#courses = ['1. DBH LOMCE','2. DBH LOMCE','3. DBH LOMCE','4. DBH LOMCE','1. Batxilergoa LOE','2. Batxilergoa LOE']
