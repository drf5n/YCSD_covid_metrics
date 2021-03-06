#!/usr/bin/env python
# coding: utf-8

# # Time Series of YCSD Covid Case Metric
# 
# This notebook examines the time series of the York County COVID Cases ostensibly used by YCSD to make decisions about school reopenings.
# 
# * YCSD presents there metrics on https://ycsd.yorkcountyschools.org/domain/1313
# * VDH represents the this number for the localities on https://www.vdh.virginia.gov/coronavirus/coronavirus/covid-19-in-virginia-locality/ and on https://www.vdh.virginia.gov/coronavirus/key-measures/pandemic-metrics/school-metrics/ under the localities tab
# * VDH shares the data at https://data.virginia.gov/Government/VDH-COVID-19-PublicUseDataset-Cases/bre9-aqqr
# * I'm sharing This notebook in Github at https://github.com/drf5n/YCSD_covid_metrics and https://github.com/drf5n/YCSD_covid_metrics/blob/master/YorkCountyCovidMetric.ipynb
# * CDC has https://beta.healthdata.gov/Community/COVID-19-State-Profile-Report-Virginia/3ghy-svgi 
# 
# -- David Forrest 2020-12-04
# 

# In[1]:


# %matplotlib widget
import os,sys,io, time, datetime, pathlib
import pandas as pd
#import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt

import bokeh.plotting
import bokeh.io
import bokeh.models
from bokeh.io import output_notebook
bokeh.io.output_notebook()


# In[2]:


def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)


# In[3]:


# get the Virginia COVID Case data from https://data.virginia.gov/Government/VDH-COVID-19-PublicUseDataset-Cases/bre9-aqqr

df_name = "VA_vdh_casedata.csv"

df=pd.read_csv(df_name)
#display(datetime.datetime.now() - pd.to_datetime(df['Report Date'].iloc[-1])   )
#display(datetime.datetime.now() - pd.to_datetime(df['Report Date'].iloc[-1])  > datetime.timedelta(days=1) )

#if 1 or file_age(df_name) > 86400/2:
if not os.path.exists(df_name) or (datetime.datetime.now() - pd.to_datetime(df['Report Date'].iloc[-1])  > datetime.timedelta(days=1)) :
    get_ipython().system("wget -O $df_name 'https://data.virginia.gov/api/views/bre9-aqqr/rows.csv?accessType=DOWNLOAD'")
    pathlib.Path(df_name).touch()
df=pd.read_csv(df_name)
df["date"] = pd.to_datetime(df['Report Date'])
last_date = df['date'].iloc[-1]

if ((datetime.datetime.now() - last_date).days  >= 1) :
    display(f"{df_name} is still old with {last_date} versus {datetime.datetime.now()}")
else:
    display(f"{df_name} is up to date at {last_date} versus {datetime.datetime.now()}")


# In[4]:



df = df.sort_values(by=['Locality', 'date'])

df['TC_diff']= df.groupby('Locality')['Total Cases'].diff().fillna(0)
df['TC_sum14']= df.groupby('Locality')['Total Cases'].diff(14).fillna(0)
df['TC_sum7']= df.groupby('Locality')['Total Cases'].diff(7).fillna(0)
df['TC_sum28']= df.groupby('Locality')['Total Cases'].diff(28).fillna(0)

display(df.head())
display(df.tail())


# In[5]:


# Read VDH population data donwloaded from https://apps.vdh.virginia.gov/HealthStats/stats.htm 
# and https://apps.vdh.virginia.gov/HealthStats/documents/xls/2018%20Pop.xls 

pop_file = '/Users/drf/Downloads/2018 Pop.xls'
if not os.path.exists(pop_file):
    get_ipython().system(' wget -O "$pop_name" https://apps.vdh.virginia.gov/HealthStats/documents/xls/2018%20Pop.xls')

popxls=pd.read_excel('/Users/drf/Downloads/2018 Pop.xls',header=[3])
popxls['FIPS']=51000+(popxls.loc[:,'Code'].fillna(0)).astype(int)  # eliminate NaNs above?
#display(popxls[popxls['Code']==199]['Population'])
#display(popxls['Locality'].str.match('York County').fillna(False))
display(popxls[popxls['Locality'].str.match('York County').fillna(False)])
display(popxls[popxls['Locality'].str.contains('Virginia Beach').fillna(False)])
#display("City:",popxls[popxls['Locality'].str.contains('City').fillna(False)])


# In[6]:


# subset for York and normalize per capita
loi='York'

VDH_pop = int(popxls[popxls['Locality'].str.match('York').fillna(False)]['Population'])
display("VDH_pop: ",VDH_pop)


dfy = df[df['Locality']=='York'].copy()
dfy['per100k_14daysum']=dfy['TC_sum14']*100000/68280  
dfy['per100k_14daysum']=dfy['TC_sum14']*100000/VDH_pop
dfy['per100k_7daysum']=dfy['TC_sum7']*100000/VDH_pop


dfy['per100k_1daymean']=dfy['TC_diff']*100000/VDH_pop
dfy['per100k_7daymean']=dfy['TC_sum7']*100000/VDH_pop/7
dfy['per100k_14daymean']=dfy['TC_sum14']*100000/VDH_pop/14
dfy['per100k_28daymean']=dfy['TC_sum28']*100000/VDH_pop/28





# for VB:

if 0:
    loi='Virginia Beach'

    dfy = df[df['Locality']=='Virginia Beach'].copy()
    dfy['per100k_14daysum']=dfy['TC_sum14']*100000/450189  


# In[7]:


dfy.tail(30)


# In[8]:


ph = dfy.plot(y='per100k_14daysum',x='date',title="York County Number of new cases per 100,000 persons \nwithin the last 14 days")

ph


# In[9]:


ph = dfy.plot(y='TC_diff',x='date',title="York County Cases, 14 day sum, per 100K")
ph


# In[10]:


TOOLTIPS = [
 #   ("index", "$index"),
 #   ("date:", "$x{%F %T}"),
    ("date:", "@date{%F}"),
    ("cases/14d/100k:","@per100k_14daysum"),
 #   ("(x,y)", "($x, $y)"),
]

vmax = (int(dfy['per100k_14daysum'].max() / 40 )+2)*40 # 

#bokeh.plotting.output_file('docs/YorkCountyCovidMetric_plot.html', mode='inline')

per100k_14daysum=bokeh.plotting.figure( tooltips=TOOLTIPS, x_axis_type='datetime')
p=bokeh.plotting.figure( x_axis_type='datetime',y_range=(0,vmax),
#                        tooltips=TOOLTIPS,formatters={"$x": "datetime"},
                        title="{} Number of new cases per 100,000 persons within the last 14 days".format(loi))

p.add_layout(bokeh.models.Title(
    text="Code: https://github.com/drf5n/YCSD_covid_metrics", text_font_style="italic"), 'above')

p.add_layout(bokeh.models.Title(
    text="https://drf5n.github.io/YCSD_covid_metrics/YorkCountyCovidMetric_plot.html", text_font_style="italic"), 'above')


hth = bokeh.models.HoverTool(tooltips=TOOLTIPS,
                             formatters={"$x": "datetime",
                                        "@date": "datetime"
                                        },
                             mode='vline',
                            )

print(hth)
print(hth.formatters)
p.add_tools(hth)
#hover = p.select(dict(type=bokeh.models.HoverTool))


#hover(tooltips=TOOLTIPS,
#)

p.add_layout(bokeh.models.BoxAnnotation(bottom=0,top=5, fill_alpha=0.4, fill_color='teal'))
p.add_layout(bokeh.models.BoxAnnotation(bottom=5,top=20, fill_alpha=0.4, fill_color='lightgreen'))
p.add_layout(bokeh.models.BoxAnnotation(bottom=20,top=50, fill_alpha=0.4, fill_color='yellow'))
p.add_layout(bokeh.models.BoxAnnotation(bottom=50,top=200, fill_alpha=0.4, fill_color='orange'))
p.add_layout(bokeh.models.BoxAnnotation(bottom=200, fill_alpha=0.4, fill_color='red'))



#p.line(dfy['date'],dfy['per100k_14daysum'])
p.line(x='date', y='per100k_14daysum',source=dfy)
#p.title()

#?p.line


# In[11]:


bokeh.plotting.show(p)


# In[12]:



bokeh.plotting.save(p,filename="docs/YorkCountyCovidMetric_plot.html")

# needs geckodriver  -- have it in conda env py3plot
bokeh.io.export_png(p, filename="docs/YorkCountyCovidMetric_plot.png")


# In[13]:


increase=(748/56.009)
inc_days=(30+31+31)

display(increase, inc_days, increase**(1/inc_days))


# In[ ]:





# In[14]:


TOOLTIPS = [
 #   ("index", "$index"),
 #   ("date:", "$x{%F %T}"),
    ("date:", "@date{%F}"),
    ("cases/d/100k:","@per100k_1daymean"),    
    ("cases/d/100k_7d:","@per100k_7daymean"),
    ("cases/d/100k_14d:","@per100k_14daymean"),
    ("cases/d/100k_28d:","@per100k_28daymean"),
 #   ("(x,y)", "($x, $y)"),
]

vmax = (int(dfy['per100k_7daysum'].max() / 40 )+2)*40/7 # 

#bokeh.plotting.output_file('docs/YorkCountyCovidMetric_per_day_plot.html', mode='inline')
#per100k_7daysum=bokeh.plotting.figure( tooltips=TOOLTIPS, x_axis_type='datetime')
pp=bokeh.plotting.figure( x_axis_type='datetime',y_range=(0,vmax),
#                        tooltips=TOOLTIPS,formatters={"$x": "datetime"},
                        title="{} Average Number of new cases per 100,000 persons over the last 7, 14 or 28 days".format(loi))

pp.add_layout(bokeh.models.Title(
    text="Code: https://github.com/drf5n/YCSD_covid_metrics", text_font_style="italic"), 'above')

pp.add_layout(bokeh.models.Title(
    text="https://drf5n.github.io/YCSD_covid_metrics/YorkCountyCovidMetric_per_day_plot.html", text_font_style="italic"), 'above')


hth = bokeh.models.HoverTool(tooltips=TOOLTIPS,
                             formatters={"$x": "datetime",
                                        "@date": "datetime"
                                        },
                             mode='mouse',
                            )

print(hth)
print(hth.formatters)
pp.add_tools(hth)
#hover = p.select(dict(type=bokeh.models.HoverTool))


#hover(tooltips=TOOLTIPS,
#)

pp.add_layout(bokeh.models.BoxAnnotation(bottom=0,top=10/7, fill_alpha=0.4, fill_color='blue'))
pp.add_layout(bokeh.models.BoxAnnotation(bottom=10/7,top=49/7, fill_alpha=0.4, fill_color='yellow'))
pp.add_layout(bokeh.models.BoxAnnotation(bottom=50/7,top=100/7, fill_alpha=0.4, fill_color='orange'))
pp.add_layout(bokeh.models.BoxAnnotation(bottom=100/7, fill_alpha=0.4, fill_color='red'))

pp.circle(x='date', y='per100k_1daymean',source=dfy,color='black',legend_label="Daily")
pp.line(x='date', y='per100k_14daymean',source=dfy,legend_label="/7d")
pp.line(x='date', y='per100k_7daymean',source=dfy,color='blue',legend_label="/14d")
pp.line(x='date', y='per100k_28daymean',source=dfy,color='green',legend_label="/28d")


#p.title()

bokeh.plotting.show(pp)

#?p.line


# In[15]:



print(bokeh.plotting.save(pp,filename="docs/YorkCountyCovidMetric_per_day_plot.html"))

# needs geckodriver  -- have it in conda env py3plot
bokeh.io.export_png(pp, filename="docs/YorkCountyCovidMetric_per_day_plot.png")


# In[16]:


#?bokeh.plotting.save


# In[ ]:




