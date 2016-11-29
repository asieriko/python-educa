# -*- coding: utf-8 -*-
import csv
import numpy as np
import matplotlib.pyplot as plt

def generate_dict():
  files = [("csv/conformidad.csv")]
  evals = {}
  evals['1']= {}
  evals['2']= {}
  #evals['3']= {}
  group = {}
  values = {}
  values['studentr']=0
  values['teacherr']=0
  values['care']=0
  values['clean']=0
  values['prom']=0
  values['more4']=0
  values['subjects70']=0
  values['notpass']=0
  #values['expulsiones']=0
  for file in files:
      with open(file,'r') as results:
        reader = csv.reader(results,delimiter=";")
        next(reader,None)
        for row in reader:
            ev={}
            ev=values.copy()
            ev['studentr']=row[1]
            ev['teacherr']=row[2]
            ev['care']=row[4]
            ev['clean']=row[5]
            ev['prom']=row[7]
            ev['more4']=row[8]
            ev['subjects70']=row[10]
            ev['notpass']=row[15]
            if row[0] not in group.keys():
                group[row[0]] = {}
            group[row[0]][row[-1]] = ev
  return group

data = generate_dict()
html='''<!DOCTYPE html>
                <html lang="eu">
                    <head>
                        <meta charset=\"utf-8\"></head><body>'''
menu = ''      
body = ''
for group in sorted(data.keys()):
    ev = sorted(list(data[group].keys()),reverse=True)
    menu += '<a href=#'+group+'>'+group+'</a><br />'
    header = '<h1 id='+group+'>'+group+'</h1><table border=5px> <tr><th>Concepto</th>'
    for i in ev:
        header += '<th>'+i+'ev</th>'
    header += '</tr>'
    studentr = '<tr><td>Relacion alumnado</td>'
    for i in ev:
        studentr += '<td>'+data[group][i]['studentr']+'</td>'
    studentr += '</tr>'
    teacherr = '<tr><td>Relacion profesorado</td>'
    for i in ev:
        teacherr += '<td>'+data[group][i]['teacherr']+'</td>'
    conf = 'No Conforme' if ((int(data[group][max(ev)]['teacherr'])+int(data[group][max(ev)]['studentr']))/2 < 5) else 'Conforme'
    teacherr += '</tr><tr><td colspan=2 style="text-align:center">'+ conf+'</td></tr>'
    care = '<tr><td>Cuidado del aula</td>'
    for i in ev:
        care += '<td>'+data[group][i]['care']+'</td>'
    care += '</tr>'
    clean = '<tr><td>Limpieza del aula</td>'
    for i in ev:
        clean += '<td>'+data[group][i]['clean']+'</td>'
    conf = 'No Conforme' if ((int(data[group][max(ev)]['care'])+int(data[group][max(ev)]['clean']))/2 < 5) else 'Conforme'
    clean += '</tr><tr><td colspan=2 style="text-align:center">'+ conf+'</td></tr>'
    prom = '<tr><td>%alumnado en promocion</td>'
    for i in ev:
        prom += '<td>'+data[group][i]['prom']+'%</td>'
    prom += '</tr>'
    more4 = '<tr><td>% alumnado con más de 4 suspensos</td>'
    for i in ev:
        more4 += '<td>'+data[group][i]['more4']+'%</td>'
    conf = 'Conforme' if float(data[group][max(ev)]['prom'])>60 and float(data[group][max(ev)]['more4']) < 20 else 'No Conforme'        
    more4 += '</tr><tr><td colspan=2 style="text-align:center">'+ conf+'</td></tr>'
    subjects70 = '<tr><td>% asignaturas con más del 70% aprobados</td>'
    for i in ev:
        subjects70 += '<td>'+data[group][i]['subjects70']+'%</td>'
    conf = 'No Conforme' if float(data[group][max(ev)]['care']) > 70 else 'Conforme'
    subjects70 += '</tr><tr><td colspan=2 style="text-align:center">'+ conf+'</td></tr>'
    notpass = '<tr><td>Numero de suspensos por alumno</td>'
    for i in ev:
        notpass += '<td>'+data[group][i]['notpass']+'</td>'
    notpass += '</tr>'
    diagrams = '<img src=eu/'+group+'-Percentage.png width="600"><br /><img src=eu/'+group+'.png width="600">'

    body += header+studentr+teacherr+care+clean+prom+more4+subjects70+notpass+'</table>'+diagrams
html += menu + body + '</body></html>'
print(html)
  