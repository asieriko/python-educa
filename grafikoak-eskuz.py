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

barcolors = ['#6CA439', '#3074AE','#517B2B', '#36521D', '#007CC3']
plt.rc('axes', facecolor='#FFFEEE', edgecolor='#4E3629')
plt.rc('patch', facecolor='#6CA439', edgecolor='#517B2B', linewidth=0)
plt.rc('figure', figsize=(16,6))
plt.rc('font', size=14.0)
plt.rc('axes', color_cycle=barcolors)
plt.rc('lines', linewidth=4)

langg='es'
studpasstitle = {'eu': 'Ikasle vs ez gainditutakoak','es':'Alumnos vs suspensos'}
promttitle = {'eu':'Promozioa','es':u'Promoción'}
cur= {'eu':'Oraingoa','es':'Actual'}
prev= {'eu':'Aurrekoa','es':'Anterior'}
avg= {'eu':'BB','es':'Prom'}
avg5 = {'eu':'BB5u','es':'Prom5a'}
langt = {'eu':'Eredu-maila','es':'Modelo-nivel'}
title = studpasstitle[langg]
title2 = promttitle[langg]
group="3P"
p=[78.6,14.3,7.1]
prom=[5,4,2,0,0,0]
riesgo= [0,0,0,2,0,0]
peligro=[0,0,0,0,0,1]
left=[0.5,1.5,2.5,3.5,4.5,5.5]
legendhist = [0,1,2,3,4,5,6]
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
plt.savefig(group + "-1. Ebaluaketa-" + langg + ".png")
plt.close()

#Euskera
langg='eu'
title = studpasstitle[langg]
title2 = promttitle[langg]
print(group+";"+str(sum(prom))+";"+str(sum(peligro)))
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
plt.savefig(group + "-1. Ebaluaketa-" + langg + ".png")
plt.close()

#3PMAR
langg='eu'
title = studpasstitle[langg]
title2 = promttitle[langg]
group="3º PMAR"
p=[16,2,1]
prom=[10,4,2,0,0,0]
riesgo= [0,0,0,2,0,0]
peligro=[0,0,0,0,0,1]
left=[0.5,1.5,2.5,3.5,4.5,5.5]
legendhist = [0,1,2,3,4,5,6]
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
plt.savefig(group + "-1. Ebaluaketa-" + langg + ".png")
plt.close()


#Asiog
langg='es'
diagram1 = pd.DataFrame([85.71,78.57,78.57,92.86,85.81,92.86,42.86],['ASL', 'ACM', 'ING', 'PRO3', 'PRO4', 'EF','VET'],columns=['Actual'])
#diagram1 = pd.DataFrame([85.71,78.57,78.57,92.86,85.81,92.86,42.86],['ESL', 'EZM', 'ING', 'PRO3', 'PRO4', 'GH','BET'],columns=['Oraingoa'])
diagram = pd.DataFrame([100,100,100,100,100,100,100],['ASL', 'ACM', 'ING', 'PRO3', 'PRO4', 'EF','VET'],columns=['Actual'])
#diagram = pd.DataFrame([100,100,100,100,100,100,100],['ESL', 'EZM', 'ING', 'PRO3', 'PRO4', 'GH','BET'],columns=['Oraingoa'])
diagram3=(diagram*5+diagram1*14)/19
diagram3.plot(kind='bar', title="3PMAR").legend(loc=4)
plt.ylim(0, 100)
plt.axhline(70)
plt.savefig('3PMAR-percentage-'+langg+'.png')
plt.close()