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

lang="es"

path = "/home/asier/Hezkuntza/SGCC/PR02 Gestion del proceso ensenanza-aprendizaje (imparticion de cursos)/PR0204 Evaluacion/Python-educa/3ebaluaketa15-16/"
name2 = " (2015-2016) Azken Ebaluazioa-mean-"+lang+".png"
name1 = " (2015-2016) Azken Ebaluazioa-percent-"+lang+".png"
name = "-Azken Ebaluazioa-"+lang+".png"


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
  
  table = Table()
  table.addElement(TableColumn(numbercolumnsrepeated=4))
  if lang=="eu":
     headers=["Atala","1. Ebaluazioa","2. Ebaluazioa","Azken Ebaluazioa"]
  else:
     headers=["Apartado","1ª Evaluación","2ª Evaluación","Evaluación Final"]
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
      tr = TableRow()
      table.addElement(tr)
      for i,val in enumerate(line):
         if i==0 and not "Konf" in val:
            tc = TableCell(stylename="Table")
            tr.addElement(tc)
            p = P(stylename=tablecontents,text=val)
         elif val=="EZ ADOS":
            tc = TableCell(stylename="Table")
            tr.addElement(tc)
            p = P(stylename=tablecontentscenterred,text=val)
         else:
            tc = TableCell(stylename="Table")
            tr.addElement(tc)	   
            p = P(stylename=tablecontentscenter,text=val)
         tc.addElement(p)

  textdoc.text.addElement(table)
  
  blankline = P(text="")
  textdoc.text.addElement(blankline)
  subjectsp = P(text="%70 baino gainditu gutxiago duten ikasgaiak")
  textdoc.text.addElement(subjectsp)
  blankline = P(text="")
  textdoc.text.addElement(blankline)
  textList = List(stylename="L1")
  
  
  file = path+"ehunekoak-Azken Ebaluazioa-2015-2016-"+group+".csv"
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
  
  for n in [name,name1]:#,name2]:
    p = P()
    textdoc.text.addElement(p)
    img_path = path+group+n
    href = textdoc.addPicture(img_path)
    f = Frame(name=group+n, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
    p.addElement(f)
    img = Image(href=href, type="simple", show="embed", actuate="onLoad")
    f.addElement(img)
   
   
def coursePage(coursename,data,lang):
  coursetitle = H(stylename=h2style,text=coursename,outlinelevel=2)
  textdoc.text.addElement(coursetitle)
  blankline = P(text="")
  textdoc.text.addElement(blankline)    
  
  prom="-All-Azken Ebaluazioa-"+lang+".png"
  percent="-All (2015-2016) Azken Ebaluazioa-percent-"+lang+".png"
  for n in [prom,percent]:
    p = P()
    textdoc.text.addElement(p)
    img_path = path+coursename+n
    href = textdoc.addPicture(img_path)
    f = Frame(name=coursename+n, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
    p.addElement(f)
    img = Image(href=href, type="simple", show="embed", actuate="onLoad")
    f.addElement(img)

  for l in ['AG','D']:#data.keys():
     coursetitle = H(stylename=h2style,text=coursename+"-"+l,outlinelevel=2)
     textdoc.text.addElement(coursetitle)
     blankline = P(text="")
     textdoc.text.addElement(blankline)   
     
     prom="-Azken Ebaluazioa-"+lang+".png"
     percent=" (2015-2016) Azken Ebaluazioa-percent-"+lang+".png"
     for n in [prom,percent]:
       p = P()
       textdoc.text.addElement(p)
       img_path = path+coursename+"-"+l+n
       href = textdoc.addPicture(img_path)
       f = Frame(name=coursename+n, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
       p.addElement(f)
       img = Image(href=href, type="simple", show="embed", actuate="onLoad")
       f.addElement(img)
     
     for g in data[l]:
       groupPage(g,lang)

def ikasgaiak():
    ikasgai = {}
    with open("ikasgaiakitzulita.csv", 'r', encoding="UTF-8") as results:
     reader = csv.reader(results)
     for row in reader:
       ikasgai[row[0]] = row[1]
    return ikasgai

  
def tutors():
  df = pd.read_csv("txostena_tutorea-dena.csv",sep=";")
  taldeak = df.Izena.unique()
  zutabeak = ['harreman1', 'harreman2', 'KonfHar', 'material','garbitasun', 'KonfGar', 'Promozionatzen', 'suspasko', 'KonfProm','Suspikasgai', 'KonfIkasgai', 'Suspikasle']
  tdata = {}
  for t in taldeak:
    dfn = df[df.Izena==t]
    l=[]
    for column in dfn[4:]:
      a=dfn[column].tolist()
      a.insert(0,column)
      l.append(a)
    tdata[t] = l[2:]
  return tdata


ikasgai=ikasgaiak()
td=tutors()  

#td["3A"]

coursegroups = OrderedDict({ '1. DBH': {'AG':['1º A','1º B', '1º C','1º D'], 'D':['1. H', '1. I',  '1. J']}, 
                 '2. DBH': {'AG':['2º A','2º B', '2º C','2º D'], 'D':['2. H', '2. I',  '2. J','2. K']},
                 '3. DBH': {'AG':['3A','3B','3C'], 'D':['3H','3I','3J','3K', '3L' ]},
                 '4. DBH': {'AG':['4A','4B','4C','4D', '4E'], 'D':['4H', '4I',  '4J','4K','4L']},
                 '3º PMAR': {'AG':['3P'], 'D':['3Q']},
                 '4º Div. Cur.': {'AG':['4P'], 'D':['4Q']},
                 '1. Batxilergoa LOE': {'AG':['Bach.1A','Bach.1B'], 'D':[ 'Batx.1H', 'Batx.1I', 'Batx.1J']},
                 '2. Batxilergoa LOE': {'AG':['Bach.2A','Bach.2B'], 'D':['Batx.2H', 'Batx.2I',  'Batx.2J']}
                 })

courses = ['1. DBH','2. DBH','3. DBH','4. DBH','4º Div. Cur.','1. Batxilergoa LOE','2. Batxilergoa LOE']
groups = ['1º A','1º B', '1º C','1º D', '1. H', '1. I',  '1. J',   
       '2º A', '2º B',  '2º C', '2º D','2. H','2. I','2. J','2. K',
       '3A','3B','3C','3H','3I','3J','3K', '3L', 
       '4A','4B','4C','4D', '4E','4H', '4I',  '4J','4K','4L',
       '4P', '4Q'
       'Bach.1A','Bach.1B', 'Batx.1H', 'Batx.1I', 'Batx.1J',
       'Bach.2A','Bach.2B','Batx.2H', 'Batx.2I',  'Batx.2J',]

for k in courses:
  coursePage(k,coursegroups[k],lang)
  
  
textdoc.save("report.odt")  

coursegroups = { '1. DBH': {'AG':['1º A','1º B', '1º C','1º D'], 'D':['1. H', '1. I',  '1. J']}, 
                 '2. DBH': {'AG':['2º A','2º B', '2º C','2º D'], 'D':['2. H', '2. I',  '2. J','2. K']},
                 '3. DBH': {'AG':['3A','3B','3C'], 'D':['3H','3I','3J','3K', '3L' ]},
                 '4. DBH': {'AG':['4A','4B','4C','4D', '4E'], 'D':['4H', '4I',  '4J','4K','4L']},
                 '4º Div. Cur.': {'AG':['4P'], 'D':['4Q']},
                 '1. Batxilergoa LOE': {'AG':['Bach.1A','Bach.1B'], 'D':[ 'Batx.1H', 'Batx.1I', 'Batx.1J']},
                 '2. Batxilergoa LOE': {'AG':['Bach.2A','Bach.2B'], 'D':['Batx.2H', 'Batx.2I',  'Batx.2J']}
                 }
  