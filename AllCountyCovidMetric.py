#!/usr/bin/env python
# coding: utf-8

# # Time Series of YCSD Covid Case Metric
# 
# This notebook examines the time series of the York County COVID Cases ostensibly used by YCSD to make decisions about school reopenings.
# 
# * YCSD presents there metrics on https://ycsd.yorkcountyschools.org/domain/1313
# * VDH represents the this number for the localities on https://www.vdh.virginia.gov/coronavirus/coronavirus/covid-19-in-virginia-locality/ and on https://www.vdh.virginia.gov/coronavirus/key-measures/pandemic-metrics/school-metrics/ under the localities tab
# * VDH shares the data at https://data.virginia.gov/Government/VDH-COVID-19-PublicUseDataset-Cases/bre9-aqqr
# * I'm sharing This notebook in Github at https://github.com/drf5n/YCSD_covid_metrics and https://drf5n.github.io/
# 
# -- David Forrest
# 

# In[1]:


# %matplotlib widget
import os,sys,io, time, pathlib,datetime
import pandas as pd, numpy as np
#import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt

import geopandas
import folium
import bokeh.plotting
import bokeh.io
import bokeh.models
from bokeh.io import output_notebook
bokeh.io.output_notebook()
today_str=datetime.datetime.now().strftime("%m/%d/%Y")


# In[2]:


def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)


# In[3]:


# get the Virginia COVID Case data from https://data.virginia.gov/Government/VDH-COVID-19-PublicUseDataset-Cases/bre9-aqqr

df_name = "VA_vdh_casedata.csv"
if file_age(df_name) > 86400:
    get_ipython().system("wget -O $df_name 'https://data.virginia.gov/api/views/bre9-aqqr/rows.csv?accessType=DOWNLOAD'")
    pathlib(df_name).touch()


# In[4]:


df=pd.read_csv(df_name)
df["date"] = pd.to_datetime(df['Report Date'])

if not df.iloc[-1]['Report Date'] == today_str:
    print(f'Datafile "{df_name}" not up to date')
    df.tail()


# In[5]:


# get the daily and 14 day sums for each locality
df = df.sort_values(by=['Locality', 'VDH Health District', 'date'])
display(df.head())

df['TC_diff']= df.groupby('Locality')['Total Cases'].diff().fillna(0)
df['TC_sum14']= df.groupby('Locality')['Total Cases'].diff(14).fillna(0)
df['TC_sum28']= df.groupby('Locality')['Total Cases'].diff(28).fillna(0)

display(df.tail())


# In[6]:


# subset for York and normalize per capita
dfy = df[df['Locality']=='York'].copy()
dfy['per100k_14daysum']=dfy['TC_sum14']*100000/67782  


# In[7]:


dfy


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


#p=bokeh.plotting.figure( tooltips=TOOLTIPS, x_axis_type='datetime')
p=bokeh.plotting.figure( x_axis_type='datetime',y_range=(0,300),
#                        tooltips=TOOLTIPS,formatters={"$x": "datetime"},
                        title="York County Number of new cases per 100,000 persons within the last 14 days")

    
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

p.add_layout(bokeh.models.BoxAnnotation(bottom=0,top=5, fill_alpha=0.4, fill_color='olive'))
p.add_layout(bokeh.models.BoxAnnotation(bottom=5,top=20, fill_alpha=0.4, fill_color='green'))
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


#bokeh.plotting.output_file('YorkCountyCovidMetric_plot.html', mode='inline')
#bokeh.plotting.save(p)

# needs geckodriver  -- have it in conda env py3plot
#bokeh.io.export_png(p, filename="YorkCountyCovidMetric_plot.png")


# In[13]:


## Save notebook as a python script:
#! jupyter nbconvert --to script AllCountyCovidMetric.ipynb


# In[14]:


# Collect populations
coest= pd.read_csv("/Users/drf/Downloads/co-est2019-alldata.csv", encoding='latin-1')
coest['FIPS']=coest['STATE']*1000+coest['COUNTY']
coest['FIPSstr']=coest['FIPS'].astype(str)


# In[15]:


coestva=coest[coest['STNAME']=="Virginia"].copy()


# In[16]:


coestva.FIPS.iloc[0]


# In[17]:


pd.set_option('display.max_rows', 500)

display(coestva[['FIPS','CTYNAME','POPESTIMATE2019']])


# In[50]:


# Normalize by population

display(df.columns)
dfpop = pd.merge(df,coestva[['FIPS','FIPSstr','CTYNAME','POPESTIMATE2019']], left_on=['FIPS'], 
                      right_on=['FIPS'],
                      how='left', sort=False)
#dfpop.set_index(['Locality','Report Date'],inplace=True)

#display(dfpop)

dfpop['caseP14P100k']=dfpop['TC_sum14']/dfpop['POPESTIMATE2019']*100000
dfpop['caseP28P100k']=dfpop['TC_sum28']/dfpop['POPESTIMATE2019']*100000


today_pop=dfpop[dfpop['Report Date']==today_str].copy()
today_pop['rank']=(-today_pop['caseP14P100k']).rank()

display(today_pop.tail(1))
display(today_pop.sort_values(by=['rank']))


# In[ ]:





# In[19]:


# from http://docs.bokeh.org/en/0.11.0/docs/gallery/choropleth.html
# bokeh.sampledata.download()
from bokeh.plotting import figure, show, output_file
from bokeh.sampledata.us_counties import data as counties
from bokeh.sampledata.us_states import data as states
from bokeh.sampledata.unemployment import data as unemployment

if 0: # bokeh chorpleths are less rich than folium annoated geojsons

    INC_STATES = ('VA')

    EXCLUDED = ("ak", "hi", "pr", "gu", "vi", "mp", "as")
    INCLUDED = ('va')

    state_xs = [states[code]["lons"] for code in states if code in INC_STATES]
    state_ys = [states[code]["lats"] for code in states if code in INC_STATES]

    county_xs=[counties[code]["lons"] for code in counties if counties[code]["state"]  in INCLUDED]
    county_ys=[counties[code]["lats"] for code in counties if counties[code]["state"]  in INCLUDED]

    colors = ["#F1EEF6", "#D4B9DA", "#C994C7", "#DF65B0", "#DD1C77", "#980043"]


# In[20]:


if 0:
    county_colors = []
    for county_id in counties:
        if counties[county_id]["state"] not in INCLUDED:
            continue
        try:
            rate = unemployment[county_id]
            idx = int(rate/6)
            county_colors.append(colors[idx])
        except KeyError:
            county_colors.append("black")

    p = figure(title="US Unemployment 2009", toolbar_location="left",
               plot_width=1100, plot_height=700)

    p.patches(county_xs, county_ys,
              fill_color=county_colors, fill_alpha=0.7,
              line_color="white", line_width=0.5)

    p.patches(state_xs, state_ys, fill_alpha=0.0,
              line_color="#884444", line_width=2, line_alpha=0.3)

    output_file("choropleth.html", title="choropleth.py example")

    show(p)


# In[21]:



# Load the shape of the zone (US states)
# Find the original file here: https://github.com/python-visualization/folium/tree/master/examples/data
# You have to download this file and set the directory where you saved it
state_geo = os.path.join('/Users/drf/Downloads/', 'counties.geojson')

# Load the unemployment value of each state
# Find the original file here: https://github.com/python-visualization/folium/tree/master/examples/data
#state_unemployment = os.path.join('/Users/y.holtz/Desktop/', 'US_Unemployment_Oct2012.csv')
#state_data = pd.read_csv(state_unemployment)

# Initialize the map:


# folium choropleths are less rich than annotated geojsons
# Add the color for the chloropleth:
if 0:
   m = folium.Map(location=[37.9, -77.9], zoom_start=7)
   m.choropleth(
    geo_data=state_geo,
    name='CovidCasesperfortnight100k',
    data=today_pop,
    columns=['FIPSstr', 'caseP14P100k'],
   # columns=['FIPS', 'POPESTIMATE2019'],
    key_on='feature.properties.GEOID',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='New Cases/14day/100k',
    bins=[5,20,50, 200,1700]

   )
#folium.LayerControl().add_to(m)


# In[22]:


state = geopandas.read_file(state_geo)


# In[23]:


today_pop
today_pop.set_index("FIPS").join(state.set_index('GEOID'))

x = state.set_index('GEOID').join(today_pop.set_index("FIPSstr"))

display(x.tail())


# In[24]:


x['foreign']= pd.cut(x['caseP28P100k'],
                       bins=[-1,5,20,100,50000],
                       labels=['Level 1, Low:  All travelers should wear a mask, stay at least 6 feet from people who are not from your household, wash your hands often or use hand sanitizer, and watch your health for signs of illness.',
                                'Level 2, Moderate: Travelers at increased risk for severe illness from COVID-19 should avoid all nonessential travel.',
                                'Level 3, High: Travelers should avoid all nonessential travel',
                                'Level 4, Very High: Travelers should avoid all travel',
                              ]).astype(str)
x['school']= pd.cut(x['caseP14P100k'],
                       bins=[-1,5,20,50,200,50000],
                       labels=['Lowest risk of transmission in schools',
                                'Lower risk of transmission in schools',
                                'Moderate risk of transmission in schools',
                                'Higher risk of transmission in schools',
                                'Highest risk of transmission in schools',
                              ]).astype(str)

x.tail()


# In[25]:


state.tail()


# In[26]:


import branca # for a colorscale


url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
county_data = f'{url}/us_county_data.csv'
county_geo = f'{url}/us_counties_20m_topo.json'



colorscale = branca.colormap.linear.YlOrRd_09.scale(0, 200)
colorscale = branca.colormap.linear.YlOrRd_09.to_step(index=[0,5,20,50, 200,500, 1000])
colorscale = branca.colormap.StepColormap(
    ['blue','green','yellow','orange','red','purple','black'], 
    index=[0,5,20,50,200,500,1000], caption='caption',vmin=0, vmax=1200,
)

colorscale=colorscale.to_linear()
#employed_series = x.set_index('FIPSstr')['caseP14P100k']

def style_function(feature):
    y=feature['properties']['caseP14P100k']
   # print(feature)
    return {
        'fillOpacity': 0.5,
        'weight': 0,
        'fillColor': '#black' if y is None else colorscale(y)
    }
colorscale


# In[ ]:





# In[27]:



#write the combined data to a file to be read
x.to_file("vaCovidCounties.geojson", driver='GeoJSON')


# Make a map out of it:
m = folium.Map(location=[37.9, -77.9], zoom_start=7)

loc = """Virginia COVID risk per CDC <a href="https://www.cdc.gov/coronavirus/2019-ncov/travelers/map-and-travel-notices.html">Foreign Travel</a> 
      and <a href="https://www.cdc.gov/coronavirus/2019-ncov/community/schools-childcare/indicators.html#interpretation">School</a> Risk Categories</a>"""
title_html = '''
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             <a href="https://github.com/drf5n/YCSD_covid_metrics">(source code)</a>
             '''.format(loc)   

folium.GeoJson(
    "vaCovidCounties.geojson",
    name='geojson',
    style_function=style_function,
    highlight_function=lambda x: {'weight': 2, 'color':'black', 'fillOpacity': 0.4,},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['Locality','date',"VDH Health District",'caseP14P100k','school','caseP28P100k','foreign',"POPESTIMATE2019"],
   #         fields=['name',"date",'per100k_28daysum','per100k_14daysum',"POPESTIMATE2019",'foreign','school'],
   #     aliases=['State','Date','Cases/28d/100kpop','Cases/14d/100kpop','2019 Population','CDC Foreign Travel Rec.','CDC School'],),
         aliases=['Locality','Date','VDH District','Cases/14d/100kpop','School Risk','Cases/28d/100kpop','CDC on Travel','Population'],
    ),    
).add_to(m)
m.add_child(colorscale)
m.get_root().html.add_child(folium.Element(title_html))
m.save('docs/va_counties_map.html')
m


# In[28]:


x.loc['51775']['caseP14P100k']


# In[29]:


#pd.describe_option('display')


# In[49]:


popxls=pd.read_excel('/Users/drf/Downloads/2018 Pop.xls',header=[3])
popxls['FIPS']=51000+(popxls.loc[:,'Code'].fillna(0)).astype(int)  # eliminate NaNs above?
popxls.tail()


# In[ ]:


type(m.get_root().html)


# In[ ]:




