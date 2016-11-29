# -*- coding: utf-8 -*-
#!/usr/bin/python

# Some helper functions

import numpy as np
import matplotlib.pyplot as plt


def flat(dic):
    '''
    Input:
    {'Gorputz Hezkuntza': {'1. Ebaluaketa': 7.928571428571429, '2. Ebaluaketa': 7.75}, 'Gaztelania eta Literatura I': {'1. Ebaluaketa': 5.285714285714286, '2. Ebaluaketa': 4.892857142857143}, 'Hezkuntza Arreta': {'1. Ebaluaketa': 6.769230769230769, '2. Ebaluaketa': 6.615384615384615}, 'Matematika I': {'1. Ebaluaketa': 4.321428571428571, '2. Ebaluaketa': 3.892857142857143}, 'Atzerriko Bigarren Hizkuntza I: Alemana': {'1. Ebaluaketa': 8.0, '2. Ebaluaketa': 8.0}}
    Output:
    [['Gorputz Hezkuntza', 7.928571428571429, 7.75], ['Gaztelania eta Literatura I', 5.285714285714286, 4.892857142857143], ['Hezkuntza Arreta', 6.769230769230769, 6.615384615384615], ['Matematika I', 4.321428571428571, 3.892857142857143], ['Atzerriko Bigarren Hizkuntza I: Alemana', 8.0, 8.0]]
    '''
    a = []
    for k in list(dic.keys()):
        b = []
        b.append(k)
        for k1 in dic[k]:
            b.append(dic[k][k1])
        a.append(b)
    return a


def langQuery(mod):
    if mod == 'D':
        language = "language='D'"
    elif mod == 'A':
        language = "language='A'"
    elif mod == 'G':
        language = "language='G'"
    elif mod == 'AG':
        language = "(language='G' OR language='A')"
    else:
        language = ""

    return language


def generateOR(name, data):
    g = "( "
    for d in data:
        g = g + name + "='" + d + "'"
        if len(data) > 1:
            g = g + " OR "
    if len(data) > 1:  # Remove the last OR (agian with " OR ".join
        g = g[:-3]
    g = g + ")"
    return g

def generateORpandas(name, data):
    g = "( "
    for d in data:
        g = g + name + "='" + d + "'"
        if len(data) > 1:
            g = g + " | "
    if len(data) > 1:  # Remove the last OR (agian with " OR ".join
        g = g[:-2]
    g = g + ")"
    return g

(df.A == 1) & (df.D == 6)

def getColumn(vector, col):
    if vector == []:
        return []
    if col > len(vector[0]):
        raise ValueError("Not so many columns")
    return [c[col] for c in vector]


def bardiagram(name, fname, data, legend):
    '''
    Input: [['Atzerriko Hizkuntza I: Ingelesa', '5', '4'], ['Hezkuntza Arreta', '7', '5'], ['Mundu garaikiderako zienztziak', '6', '6'], ['Gaztelania eta Literatura I', '4', '4'], ['Filosofia eta herritartarsuna', '1', '6'], ['Gorputz Hezkuntza', '9', '9'], ['Fisika eta Kimika', '5', '2'], ['Teknologia industriala I', '5', '4'], ['Matematika I', '2', '2'], ['Marrazketa Teknikoa I', '3', '2'], ['BB', '4.7', '4.4']]
    Output: A bar diagram with X subjects, and columns for each evaluation period, and the average grade
    '''
    plt.clf()
    l = len(data[0])
    colors = ['#6CA439','#FF9C42','#FF4848','#3074AE']
    ind = np.arange(len(data))    # the x locations for the groups
    width = 0.3       # the width of the bars: can also be len(x) sequence
    for i in range(l - 1):
        plt.bar(ind + i * width, [float(b[i + 1]) for b in data], width,
        color=colors[i], label=legend[i])
    #plt.bar(ind+2*width, eb2, width, color='y',label='2. Ebaluaketa')
    plt.ylabel('Notak')
    plt.title(name + '\nKurtsoaren garapena')
    plt.xticks(ind + (l - 1) * width / 2, [b[0] for b in data], rotation=90)
    plt.yticks(np.arange(0, 11, 1))
    plt.subplots_adjust(bottom=0.20)
    plt.legend()
    plt.savefig(fname, format="png")
    #plt.show()


def piediagram(fname, title, data):
    plt.clf()
    legendpie = ("<=2", "3-4", "=>5")
    # Append the number in data so it can be easily compared.
    colors = ['#6CA439','#FF9C42','#FF4848']# ['green', 'orange', 'red']
    total = sum(data)
    plt.pie(data, labels=legendpie, colors=colors) #  ,autopct=lambda(p): '{:.0f}'.format(p * total / 100))
    plt.axis('equal')
    plt.title(title)
    #plt.show()
    plt.savefig(fname, format="png")
    plt.close()