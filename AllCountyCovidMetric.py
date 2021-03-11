#!/usr/bin/env python
# coding: utf-8

# # Covid Case Metrics for Virginia Counties
# 
# This notebook examines the COVID Cases in Virginia and compares them to the CDC's School Transmission Risk thresholds and the CDC's Foreign travel risk thresholds.
# 
# * YCSD presents their school metrics on https://ycsd.yorkcountyschools.org/domain/1313
# * VDH represents the this number for the localities on https://www.vdh.virginia.gov/coronavirus/coronavirus/covid-19-in-virginia-locality/ and on https://www.vdh.virginia.gov/coronavirus/key-measures/pandemic-metrics/school-metrics/ The threshold for "Highest risk of tranmission in schools is 200cases/14days/100k.
# * VDH shares the data at https://data.virginia.gov/Government/VDH-COVID-19-PublicUseDataset-Cases/bre9-aqqr
# * The CDC Foreign travel page is https://www.cdc.gov/coronavirus/2019-ncov/travelers/map-and-travel-notices.html -- the threshold for "Level 4, Very High: Avoid all travel" is 100cases/28days/100k.
# * I'm sharing This notebook in Github at https://github.com/drf5n/YCSD_covid_metrics and the graphics at https://drf5n.github.io/YCSD_covid_metrics/index.html
# 
# The CDC's highest school transmission risk level is 1/4 as strict as the CDC's foreign travel threshold, with half the sampling period (14 days vs 28 days) and twice the numerical limit (200cases/100k vs 100cases/100k)
# 
# Nearly all of the Virginia counties are far into the "Highest risk of transmission in schools"
# 
# ![image.png](attachment:1647839b-428d-4bc1-8301-cb7335a0951b.png)
# 
# (Live map at https://drf5n.github.io/YCSD_covid_metrics/va_counties_map.html)
# 
# ![image.png](attachment:c1184ad6-33e3-44de-8b91-adaabd2469b0.png)
# 
# (Live map at https://drf5n.github.io/YCSD_covid_metrics/va_counties_map_foreign.html)
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
today_str=(datetime.datetime.now()-datetime.timedelta(hours=28)).strftime("%m/%d/%Y")


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
df = df.sort_values(by=['Locality', 'date'])
display(df.head())

# get the 1day, 14 day, and 28day sums:
df['TC_diff']= df.groupby('Locality')['Total Cases'].diff().fillna(0)
df['TC_sum7']= df.groupby('Locality')['Total Cases'].diff(7).fillna(0)
df['TC_sum14']= df.groupby('Locality')['Total Cases'].diff(14).fillna(0)
df['TC_sum28']= df.groupby('Locality')['Total Cases'].diff(28).fillna(0)

display(df.tail())


# In[6]:


# Use population estimates from https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/ 
coest= pd.read_csv("/Users/drf/Downloads/co-est2019-alldata.csv", encoding='latin-1')
coest['FIPS']=coest['STATE']*1000+coest['COUNTY']
coest['FIPSstr']=coest['FIPS'].astype(str)


# In[7]:


# subset for Virginia
coestva=coest[coest['STNAME']=="Virginia"].copy()


# In[8]:


coestva.FIPS.iloc[0]


# In[9]:


pd.set_option('display.max_rows', 500)

display(coestva[['FIPS','CTYNAME','POPESTIMATE2019']])


# In[10]:


# Normalize Covid cases by population

display(df.columns)
dfpop = pd.merge(df,coestva[['FIPS','FIPSstr','CTYNAME','POPESTIMATE2019']], left_on=['FIPS'], 
                      right_on=['FIPS'],
                      how='left', sort=False)
#dfpop.set_index(['Locality','Report Date'],inplace=True)

#display(dfpop)

dfpop['caseP7P100k']=dfpop['TC_sum7']/dfpop['POPESTIMATE2019']*100000
dfpop['caseP14P100k']=dfpop['TC_sum14']/dfpop['POPESTIMATE2019']*100000
dfpop['caseP28P100k']=dfpop['TC_sum28']/dfpop['POPESTIMATE2019']*100000


today_pop=dfpop[dfpop['Report Date']==today_str].copy()
today_pop['rank']=(-today_pop['caseP28P100k']).rank()

display(today_pop.tail(1))
#display(today_pop.sort_values(by=['rank']))


# In[11]:


#dfpop[dfpop['Locality']=='Charlottesville']


# In[12]:


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


# In[13]:


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


# In[14]:



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


# In[15]:


state = geopandas.read_file(state_geo)


# In[16]:


today_pop
today_pop.set_index("FIPS").join(state.set_index('GEOID'))

x = state.set_index('GEOID').join(today_pop.set_index("FIPSstr"))

display(x.tail())


# In[17]:


x['foreign']= pd.cut(x['caseP28P100k'],
                       bins=[-1,5,20,100,50000],
                       labels=[
                           #'Level 1, Low:  All travelers should wear a mask, stay at least 6 feet from people who are not from your household, wash your hands often or use hand sanitizer, and watch your health for signs of illness.',
                           'Level 1, Low:  All travelers should wear a mask,...',
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
x['newschool']= pd.cut(x['caseP7P100k'],
                       bins=[-1,10,25,100,50000],
                       labels=['Low risk of transmission in schools',
                                'Moderate risk of transmission in schools',
                                'Substantial risk of transmission in schools',
                                'High risk of transmission in schools',
                              ]).astype(str)

x.tail()


# In[18]:


#x[x['Locality']=='Nelson']


# In[19]:


state.tail()


# In[20]:


import branca # for a colorscale


url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
county_data = f'{url}/us_county_data.csv'
county_geo = f'{url}/us_counties_20m_topo.json'



colorscale = branca.colormap.linear.YlOrRd_09.scale(0, 200)
colorscale = branca.colormap.linear.YlOrRd_09.to_step(index=[0,5,20,50, 200,500, 1000])
colorscale = branca.colormap.StepColormap(
    ['blue','green','yellow','orange','red','red','black'], 
    index=[0,5,20,50,200,250,1000], caption='New Cases/14days/100k',vmin=0, vmax=1000,
)


colorscale14=colorscale.to_linear()
colorscale14.caption='New Cases/14days/100k'  # reset caption
#employed_series = x.set_index('FIPSstr')['caseP14P100k']

def style_function14(feature):
    y=feature['properties']['caseP14P100k']
   # print(feature)
    return {
        'fillOpacity': 0.5,
        'weight': 0,
        'fillColor': '#black' if y is None else colorscale14(y)
    }

colorscale28 = branca.colormap.StepColormap(
    ['blue','green','yellow','orange','red','red','black'], 
    index=[0,5,20,50,100,250,1000], caption='New Cases/28days/100k',vmin=0, vmax=1000,
).to_linear()
colorscale28.caption='New Cases/28days/100k'  # reset caption



def style_function28(feature):
    y=feature['properties']['caseP28P100k']
   # print(feature)
    return {
        'fillOpacity': 0.5,
        'weight': 0,
        'fillColor': '#black' if y is None else colorscale28(y)
    }

colorscale7 = branca.colormap.StepColormap(
    ['blue','yellow','orange','red','red','black'], 
    index=[0,10,25,50,125,500], caption='New Cases/7days/100k',vmin=0, vmax=500,
).to_linear()
colorscale7.caption='New Cases/7days/100k'  # reset caption

colorscale7b = branca.colormap.StepColormap(
    ['blue','yellow','orange','red','red','black'], 
    index=[0,10,25,50,125,500], caption='New Cases/7days/100k',vmin=0, vmax=200,
) .to_linear()
colorscale7b.caption='New Cases/7days/100k'  # reset caption



def style_function7(feature):
    y=feature['properties']['caseP7P100k']
   # print(feature)
    return {
        'fillOpacity': 0.5,
        'weight': 0,
        'fillColor': '#black' if y is None else colorscale7(y)
    }




colorscale7b


# In[21]:


colorscale.caption


# In[22]:



#write the combined data to a file to be read
x.to_file("vaCovidCounties.geojson", driver='GeoJSON')


# Make a map out of it:
m = folium.Map(location=[37.9, -77.9], zoom_start=7)

loc = """Virginia COVID risk per CDC <a href="https://www.cdc.gov/coronavirus/2019-ncov/community/schools-childcare/indicators.html#interpretation">School</a> Risk Categories (school colors)"""
subt = """(Red is CDC >200cases/14days/100k, "Highest Risk of Transmission in schools" and Black is 5x higher)"""
title_html = '''
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             <h4 align="center" style="font-size:12px"><b>{}</b></h4>
             
             <a href="https://github.com/drf5n/YCSD_covid_metrics/">(source code)</a>
             '''.format(loc,subt)   

folium.GeoJson(
    "vaCovidCounties.geojson",
    name='geojson',
    style_function=style_function14,
    highlight_function=lambda x: {'weight': 2, 'color':'black', 'fillOpacity': 0.4,},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['Locality','date',"VDH Health District",'caseP7P100k','caseP14P100k','school','caseP28P100k','foreign',"POPESTIMATE2019"],
   #         fields=['name',"date",'per100k_28daysum','per100k_14daysum',"POPESTIMATE2019",'foreign','school'],
   #     aliases=['State','Date','Cases/28d/100kpop','Cases/14d/100kpop','2019 Population','CDC Foreign Travel Rec.','CDC School'],),
         aliases=['Locality','Date','VDH District','Cases/7d/100kpop','Cases/14d/100kpop','School Risk','Cases/28d/100kpop','CDC on Travel','Population'],
    ),    
).add_to(m)
m.add_child(colorscale14)
m.get_root().html.add_child(folium.Element(title_html))
m.save('docs/va_counties_map.html')
m


# In[23]:


# New CDC school colors (7 day window)
#write the combined data to a file to be read
x.to_file("vaCovidCounties7.geojson", driver='GeoJSON')


# Make a map out of it:
m = folium.Map(location=[37.9, -77.9], zoom_start=7)

loc = """Virginia COVID risk per new CDC <a href="https://www.cdc.gov/coronavirus/2019-ncov/community/schools-childcare/indicators.html#interpretation">School</a> Risk Categories (school colors)"""
subt = """(Red is CDC >100cases/7days/100k, "High Risk of Transmission in schools" and Black is 5x higher)"""
title_html = '''
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             <h4 align="center" style="font-size:12px"><b>{}</b></h4>
             
             <a href="https://github.com/drf5n/YCSD_covid_metrics/">(source code)</a>
             '''.format(loc,subt)   

folium.GeoJson(
    "vaCovidCounties.geojson",
    name='geojson',
    style_function=style_function7,
    highlight_function=lambda x: {'weight': 2, 'color':'black', 'fillOpacity': 0.4,},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['Locality','date',"VDH Health District",'caseP7P100k','newschool','caseP14P100k','school','caseP28P100k','foreign',"POPESTIMATE2019"],
   #         fields=['name',"date",'per100k_28daysum','per100k_14daysum',"POPESTIMATE2019",'foreign','school'],
   #     aliases=['State','Date','Cases/28d/100kpop','Cases/14d/100kpop','2019 Population','CDC Foreign Travel Rec.','CDC School'],),
         aliases=['Locality','Date','VDH District','Cases/7d/100kpop','School Risk (feb)','Cases/14d/100kpop','School Risk','Cases/28d/100kpop','CDC on Travel','Population'],
    ),    
).add_to(m)
m.add_child(colorscale7b)
m.get_root().html.add_child(folium.Element(title_html))
m.save('docs/va_counties_map7.html')
m


# In[24]:



#write the combined data to a file to be read
x.to_file("vaCovidCounties.geojson", driver='GeoJSON')


# Make a map out of it:
m = folium.Map(location=[37.9, -77.9], zoom_start=7)

loc = """Virginia COVID risk colored per CDC <a href="https://www.cdc.gov/coronavirus/2019-ncov/travelers/map-and-travel-notices.html">Foreign Travel</a> 
       Risk Categories """
subt = """(Red is CDC Level 4: >100cases/28days/100k, Very High, Avoid all travel" and Black is 10x higher)"""
title_html = '''
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             <h4 align="center" style="font-size:12px"><b>{}</b></h4>
             
             <a href="https://github.com/drf5n/YCSD_covid_metrics/">(source code)</a>
             '''.format(loc,subt)   

folium.GeoJson(
    "vaCovidCounties.geojson",
    name='geojson',
    style_function=style_function28,
    highlight_function=lambda x: {'weight': 2, 'color':'black', 'fillOpacity': 0.4,},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['Locality','date',"VDH Health District",'caseP7P100k','caseP14P100k','school','caseP28P100k','foreign',"POPESTIMATE2019"],
   #         fields=['name',"date",'per100k_28daysum','per100k_14daysum',"POPESTIMATE2019",'foreign','school'],
   #     aliases=['State','Date','Cases/28d/100kpop','Cases/14d/100kpop','2019 Population','CDC Foreign Travel Rec.','CDC School'],),
         aliases=['Locality','Date','VDH District','Cases/7d/100kpop','Cases/14d/100kpop','School Risk','Cases/28d/100kpop','CDC on Travel','Population'],
    ),    
).add_to(m)
m.add_child(colorscale28)
m.get_root().html.add_child(folium.Element(title_html))
m.save('docs/va_counties_map_foreign.html')
m


# In[25]:


x.loc['51775']['caseP14P100k']


# In[26]:


#pd.describe_option('display')


# In[27]:


popxls=pd.read_excel('/Users/drf/Downloads/2018 Pop.xls',header=[3])
popxls['FIPS']=51000+(popxls.loc[:,'Code'].fillna(0)).astype(int)  # eliminate NaNs above?
popxls.tail()


# In[28]:


type(m.get_root().html)


# In[ ]:





# In[ ]:




