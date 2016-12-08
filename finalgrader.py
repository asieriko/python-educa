# coding: utf-8
# In[1]:

import pandas as pd


# In[73]:
d = {'year' : pd.Series(["2015-2016", "2015-2016", "2015-2016","2015-2016","2015-2016","2015-2016","2015-2016"]),
      'student' : pd.Series(["john","john","john","john","john","michael","michael"]),
      'subject' : pd.Series(["Math","Math","Fis","Fis","ICT","Fis","Fis"]),
      'period' : pd.Series(["Az","EO","Az","EO","Az","Az","EO"]),
      'grade' : pd.Series([2,5,4,6,10,3,8]),}
df = pd.DataFrame(d)
grouped = df.groupby(['year','student','subject'])

# In[219]:

def finalgrade(x):
    print(x)
    if 'EO' in x[["period","grade"]].period.unique():
        print('EO',int(x[x.period=='EO'].grade))
        df = x[x.period=="EO"]
        df.period = "Final"
        return df
    else:
        df = x[x.period=="Az"]
        df.period = "Final"
        return df


# In[220]:

newrows = grouped.apply(finalgrade)

# In[209]:

nr = newrows.reset_index()

# In[232]:

for year in df.year.unique():
    for student in df[df.year==year].student.unique():
        for subject in df[(df.year==year)&(df.student==student)].subject.unique():
            #print(df[(df.year==year)&(df.student==student)&(df.subject==subject)])
            if 'EO' in df[(df.year==year)&(df.student==student)&(df.subject==subject)].period.unique():
                print(df[(df.year==year)&(df.student==student)&(df.subject==subject)&(df.period=='EO')])
                df2 = df[(df.year==year)&(df.student==student)&(df.subject==subject)&(df.period=='EO')]
                df2.period = "Final"
                #Maybe create a new one instead of concat, at least if is going to store in the database
                #by updating it, so it doesn't have to be calculated every time
                df = pd.concat([df,df2])
            else:
                print(df[(df.year==year)&(df.student==student)&(df.subject==subject)&(df.period=='Az')])
                df2 = df[(df.year==year)&(df.student==student)&(df.subject==subject)&(df.period=='Az')]
                df2.period = "Final"
                df = pd.concat([df,df2])


# In[235]:

df.reset_index().drop('index',1)


# In[237]:

df[df.period=="Final"]


# In[ ]:



# In[210]:

def finalgrade(x):
    if 'EO' in x[["period","grade"]].period.unique():
        print('EO',int(x[x.period=='EO'].grade))
        return int(x[x.period=='EO'].grade)
    else:
        print('Az',int(x[x.period=='Az'].grade))
        return int(x[x.period=='Az'].grade)
