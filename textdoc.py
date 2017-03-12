'''
This class provides a simple and easy interface for odfpy
It allows simple adding of elements without understanding
the underlying Standard.
It lacks, for now, the ability to edit paragraph styles
without editing this file
author: Asier Urío Larrea
email: asieriko at gmail dot com
License: GPL v2 or later?
'''

from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties, ParagraphProperties, GraphicProperties, TableCellProperties, HeaderFooterProperties
from odf.style import PageLayout, MasterPage, Header, Footer, HeaderStyle, PageLayoutProperties, FooterStyle
from odf.text import P, H, List, ListItem, PageNumber
from odf.draw  import Page, Frame, TextBox, Image
from odf.table import Table, TableColumn, TableRow, TableCell

class textdoc:

    def __init__(self):
        self.textdoc = OpenDocumentText()
        
        self.oneandhalflines = Style(name="oneandhalflines", parentstylename="Standard", family="paragraph")
        self.oneandhalflines.addElement(ParagraphProperties(lineheight="1.5"))
        self.textdoc.automaticstyles.addElement(self.oneandhalflines)
        
        # Create a style for the paragraph with page-break
        self.withbreak = Style(name="WithBreak", parentstylename="Standard", family="paragraph")
        self.withbreak.addElement(ParagraphProperties(breakbefore="page"))
        self.textdoc.automaticstyles.addElement(self.withbreak)

        self.footercenterstyle = Style(name="footercenter", family="paragraph", parentstylename="Standard")
        self.footercenterstyle.addElement(ParagraphProperties(textalign="center"))
        self.textdoc.automaticstyles.addElement(self.footercenterstyle)

        self.footerstyle = FooterStyle()
        self.footerstyle.addElement(HeaderFooterProperties(padding="0.05cm",borderleft="none",borderright="none",bordertop="none",borderbottom="none",shadow="none", minheight="1cm"))

        #Text Header
        self.plheaderstyle = PageLayout(name="pl")
        self.plheaderstyle.addElement(PageLayoutProperties(marginleft="2cm",marginright="2cm",margintop="1cm",marginbottom="1cm"))
        self.headerstyle = HeaderStyle()
        self.headerstyle.addElement(HeaderFooterProperties(backgroundcolor="#e6e6ff",padding="0.05cm",borderleft="none",borderright="none",bordertop="none",borderbottom="2.01pt solid #000099",shadow="none", minheight="1cm"))
        self.plheaderstyle.addElement(self.headerstyle)
        self.plheaderstyle.addElement(self.footerstyle)
        self.textdoc.automaticstyles.addElement(self.plheaderstyle)
        
        #image header
        self.pliheaderstyle = PageLayout(name="pli")
        self.pliheaderstyle.addElement(PageLayoutProperties(marginleft="2cm",marginright="2cm",margintop="1cm",marginbottom="1cm"))
        self.headeristyle = HeaderStyle()
        self.headeristyle.addElement(HeaderFooterProperties(padding="0.05cm",borderleft="none",borderright="none",bordertop="none",borderbottom="none",shadow="none", minheight="2cm"))
        self.pliheaderstyle.addElement(self.headeristyle)
        self.pliheaderstyle.addElement(self.footerstyle)   
        self.textdoc.automaticstyles.addElement(self.pliheaderstyle)
        
        self.h1style = Style(name="Heading 1",  family="paragraph",parentstylename="Heading 1")
        self.h1style.addElement(GraphicProperties(fill="solid",fillcolor="#e6e6ff"))
        self.h1style.addElement(TextProperties(attributes={'fontsize':"14pt",'fontweight':"bold",'color':"#000099" }))
        self.h1style.addElement(ParagraphProperties(breakbefore="page",margintop="0.4cm",marginbottom="0.2cm",backgroundcolor="#e6e6ff",padding="0.05cm",borderleft="none",borderright="none",bordertop="none",borderbottom="2.01pt solid #000099",shadow="none"))
        self.textdoc.automaticstyles.addElement(self.h1style)

        self.h2style = Style(name="Heading 2", family="paragraph",parentstylename="Heading 2")
        self.h2style.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold",'color':"#000099" }))
        self.h2style.addElement(ParagraphProperties(marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
        self.textdoc.automaticstyles.addElement(self.h2style)
        
        self.h2bstyle = Style(name="Heading 2", family="paragraph",parentstylename="Heading 2")
        self.h2bstyle.addElement(ParagraphProperties(breakbefore="page",marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
        self.textdoc.automaticstyles.addElement(self.h2bstyle)

        self.h3style = Style(name="Heading 3", family="paragraph",parentstylename="Heading 3")
        self.h3style.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold",'color':"#000099" }))
        self.h3style.addElement(ParagraphProperties(marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
        self.textdoc.automaticstyles.addElement(self.h3style)
        self.h3bstyle = Style(name="Heading 3", family="paragraph",parentstylename="Heading 3")
        self.h3bstyle.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold",'color':"#000099" }))
        self.h3bstyle.addElement(ParagraphProperties(breakbefore="page",marginleft="0cm",marginright="0cm",margintop="0.2cm",marginbottom="0.2cm",lineheight="150%",textindent="1.2cm",autotextindent="false"))
        self.textdoc.automaticstyles.addElement(self.h3bstyle)

        self.TAB_style = Style(name="Table", family="table-cell", parentstylename="Standard")
        self.TAB_style.addElement(TableCellProperties(border="0.05pt solid #000000"))
        self.textdoc.automaticstyles.addElement(self.TAB_style)

        self.TAB_stylered = Style(name="Table red", family="table-cell", parentstylename="Standard")
        self.TAB_stylered.addElement(TableCellProperties(backgroundcolor="ff0000",border="0.05pt solid #000000"))
        self.textdoc.automaticstyles.addElement(self.TAB_stylered)

        self.tableheaders = Style(name="Table Headers", family="paragraph", parentstylename="Standard")
        self.tableheaders.addElement(ParagraphProperties(numberlines="false", linenumber="0",textalign="center",margintop="0.2cm",marginbottom="0.2cm"))
        self.tableheaders.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold"}))
        self.textdoc.styles.addElement(self.tableheaders)

        self.tablecontents = Style(name="Table Contents", family="paragraph", parentstylename="Standard")
        self.tablecontents.addElement(ParagraphProperties(numberlines="false", linenumber="0",margintop="0.2cm",marginbottom="0.2cm"))
        self.tablecontents.addElement(TextProperties(attributes={'fontsize':"12pt" }))
        self.textdoc.styles.addElement(self.tablecontents)

        self.tablecontentscenter = Style(name="Table Contents Center", family="paragraph", parentstylename="Standard")
        self.tablecontentscenter.addElement(ParagraphProperties(numberlines="false", linenumber="0", textalign="center",margintop="0.2cm",marginbottom="0.2cm"))
        self.tablecontentscenter.addElement(TextProperties(attributes={'fontsize':"12pt" }))
        self.textdoc.styles.addElement(self.tablecontentscenter)

        self.tablecontentscenterred = Style(name="Table Contents Center Red", family="paragraph", parentstylename="Standard")
        self.tablecontentscenterred.addElement(ParagraphProperties(numberlines="false", linenumber="0", textalign="center", backgroundcolor="#ff0000",margintop="0.2cm",marginbottom="0.2cm"))
        self.tablecontentscenterred.addElement(TextProperties(attributes={'fontsize':"12pt" }))
        self.textdoc.styles.addElement(self.tablecontentscenterred)
        
    def addTitle(self,text):
        title = H(stylename=self.h1style,text=text,outlinelevel=1)
        self.textdoc.text.addElement(title)
    
    def addTitle2(self,text,newpage=False):
        if newpage:
            title = H(stylename=self.h2bstyle,text=text,outlinelevel=2)
        else:
            title = H(stylename=self.h2style,text=text,outlinelevel=2)
        self.textdoc.text.addElement(title)
        
    def addTitle3(self,text,newpage=False):
        if newpage:
            title = H(stylename=self.h3bstyle,text=text,outlinelevel=3)
        else:
            title = H(stylename=self.h3style,text=text,outlinelevel=3)
        self.textdoc.text.addElement(title)
        
    def addParagraph(self,text):
        #paragraph = P(stylename=self.oneandhalflines,text=text)
        paragraph = P(text=text)
        self.textdoc.text.addElement(paragraph) 
        
    def addBlankLine(self):
        self.addParagraph("")
        
    def addImage(self,image_path,name):
        if not name:
            name = image_path
        p = P()
        self.textdoc.text.addElement(p)
        href = self.textdoc.addPicture(image_path)
        f = Frame(name=name, anchortype="paragraph", width="17cm", height="7.5cm", zindex="0")
        p.addElement(f)
        img = Image(href=href, type="simple", show="embed", actuate="onLoad")
        f.addElement(img)
        
    def addNewPage(self):
        breakpage = P(stylename=self.withbreak,text="")
        self.textdoc.text.addElement(breakpage)
        
    def addList(self,elements):
        textList = List(stylename="L1")
        for element in elements:
         item = ListItem()
         item.addElement(P(text=element))
         textList.addElement(item)
        self.textdoc.text.addElement(textList)
        
    def addTable(self,tabledata,headers,formater=None):
        if formater and len(formater)!=len(tabledata):
            raise ValueError
        if formater is None:
            formater = [[""]*len(tabledata[0])]*len(tabledata)
        table = Table()
        columns = len(headers)
        table.addElement(TableColumn(numbercolumnsrepeated=columns))
        tr = TableRow()
        table.addElement(tr)
        for header in headers:
            tc = TableCell(stylename="Table")
            tr.addElement(tc)
            p = P(stylename=self.tableheaders,text=header)
            tc.addElement(p)
        for line,formats in zip(tabledata,formater):
            tr = TableRow()
            table.addElement(tr)
            for column,cformat in zip(line,formats):
                if cformat == "centerred":
                    cellformat = self.tablecontentscenter
                elif cformat == "center":
                    cellformat = self.tablecontentscenterred
                else:
                    cellformat = self.tablecontents
                tc = TableCell(stylename="Table")
                tr.addElement(tc)
                p = P(stylename=cellformat,text=column)
                tc.addElement(p)
        self.textdoc.text.addElement(table)

    def addHeaderFooter(self,header=None,footer=None):
        if header or footer:
            mp = MasterPage(name="Standard", pagelayoutname=self.plheaderstyle)
            self.textdoc.masterstyles.addElement(mp)
            if header:
                h = Header()
                hp = P(text=header)#,stylename=self.headerstyle)
                h.addElement(hp)
                mp.addElement(h)
            if footer:
                f = Footer()
                fp = P(text=footer,stylename=self.footercenterstyle)
                f.addElement(fp)
                mp.addElement(f)
        
    def addImageHeaderFooter(self,header=None,footer=None):
        if header or footer:
            mp = MasterPage(name="Standard", pagelayoutname=self.pliheaderstyle)
            self.textdoc.masterstyles.addElement(mp)
            if header:
                h = Header()
                p = P()
                href = self.textdoc.addPicture(header)
                f = Frame(name="membrete", anchortype="paragraph", width="17cm", height="1.5cm", zindex="0")
                p.addElement(f)
                img = Image(href=href, type="simple", show="embed", actuate="onLoad")
                f.addElement(img)
                h.addElement(p)
                
                mp.addElement(h)
            if footer:
                fo = Footer()
                pn = PageNumber()
                fp = P(text=footer,stylename=self.footercenterstyle)#FIXME: Pagen number shoulb be better
                fp.addElement(pn)
                fo.addElement(fp)
                mp.addElement(fo)
        
        
    def save(self,filename):
        self.textdoc.save(filename)
