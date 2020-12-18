#!/usr/bin/env python
# coding: utf-8

# # COVID by State, colored per CDC foreign travel advisory map

# On the CDC page https://www.cdc.gov/coronavirus/2019-ncov/travelers/map-and-travel-notices.html the CDC communicates foreign travel advisories on a map like this
# 
# ![image.png](attachment:4796c9de-5ddc-421b-93b2-025fd7e7e27b.png)
# 
# But on the US page, the CDC uses cooler, calmer colors, with 4x higher thresholds to make a map like this:
# 
# ![image.png](attachment:81415972-bda3-40ee-9f13-3be412686587.png)
# 
# I'm curious how the foreign travel advisory thresholds would look for a US Map.
# 
# Based on https://www.cdc.gov/coronavirus/2019-ncov/travelers/how-level-is-determined.html the color scheme is:
# 
# * Dark Red: Very High,  >100cases/28days/100kpop -- Travelers should avoid all travel...
# * Dark Orange: High, >50cases/28days/100kpop -- Travelers should avoid all nonessential travel...
# * Light Orange: Moderate, >5cases/28days/100kpop -- Travelers at increased risk for severe illness from COVID-19 should avoid all nonessential travel...
# * Yellow: Low, <5cases/28days/100kpop -- All travelers should wear a mask, stay at least 6 feet from people who are not from your household, wash your hands often or use hand sanitizer, and watch your health for signs of illness.
# 
# I was successful, and I have posted this notebook on Github at https://github.com/drf5n/YCSD_covid_metrics/blob/master/CovidStates.ipynb with the map published on https://drf5n.github.io/ and https://drf5n.github.io/us_covid_states_map.html  It looks like this:
# 
# ![image.png](attachment:02decef1-273c-419d-a7ac-87761f332983.png)
# 
# Every single state in the US is above the 100cases/28days/100kpop level of COVID transmission that, for CDC foreign travel advisories, is in the "Level 4, Very High: Travelers should avoid all travel" range.  
# 
# The school transmission risk criteria is 4x more lax, with a the highest risk level allowing twice the cases in half the time: 200cases/14days/100kpop. Under the school criteria, only Vermont, at 174 cases/14days/100kpop, and Hawaii at 99cases/14days/100kpop aren't above the highest risk threshold for school transmission.
# 
# -- drf 2020-12-04

# In[1]:


import os,geopandas, folium,datetime
import branca # for a colorscale
import pandas as pd


# In[2]:


# Downloaded state data from https://github.com/python-visualization/folium/blob/master/examples/data/us-states.json
state_json=os.path.join('/Users/drf/Downloads/', 'us-states.json')
state = geopandas.read_file(state_json)


# In[3]:


# #downloaded population data from Census https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/state/detail/

census_pop_state_file=os.path.join('/Users/drf/Downloads/', 'SCPRC-EST2019-18+POP-RES.csv')

pops = pd.read_csv(census_pop_state_file)
#display(pops)


# In[4]:


# map 2-letter codes to population data using https://github.com/drf5n/fips-codes/blob/patch-1/state_fips_master.csv modded from 
# https://github.com/kjhealy/fips-codes/blob/master/state_fips_master.csv
statemaster = pd.read_csv('https://raw.githubusercontent.com/drf5n/fips-codes/patch-1/state_fips_master.csv')
pop_augment = pops.set_index('STATE').join(statemaster.set_index('state')['state_abbr']).reset_index()
display(pop_augment)


# In[5]:


# Download the state-level covid case histories from...  

covids = pd.read_json('https://api.covidtracking.com/v1/states/daily.json')

#covids["date"] = pd.to_datetime(covids['date'])
display(covids)



# In[6]:


lastdate = int(covids.tail(1).date) # last day in file
#doi = lastdate # (bad as updates happen)
doi = int((datetime.datetime.now()-datetime.timedelta(days = 1)
         ).strftime("%Y%m%d"))  # yesterday morning as an int
display(doi)


# In[7]:


df = covids.sort_values(by=['state', 'date'])
display(df)

df['TC_diff']= df.groupby('state')['positive'].diff().fillna(0)
df['TC_sum14']= df.groupby('state')['positive'].diff(14).fillna(0)
df['TC_sum28']= df.groupby('state')['positive'].diff(28).fillna(0)

display(df)

dfy = df[df['date']==doi].copy()
display("DFY:",dfy)

dfya = dfy.set_index('state').join(pop_augment.set_index('state_abbr'),lsuffix='lj').reset_index()

dfya['per100k_14daysum']=dfya['TC_sum14']*100000/dfya['POPESTIMATE2019']
dfya['per100k_28daysum']=dfya['TC_sum28']*100000/dfya['POPESTIMATE2019']
dfya['per100k_1daysum']=dfya['TC_diff']*100000/dfya['POPESTIMATE2019']
display(dfya.columns)

display(dfya[['state','date','per100k_1daysum','per100k_14daysum', 'per100k_28daysum']])

dfya['foreign']= pd.cut(dfya['per100k_28daysum'],
                       bins=[-1,5,20,100,50000],
                       labels=['Level 1, Low:  All travelers should wear a mask, stay at least 6 feet from people who are not from your household, wash your hands often or use hand sanitizer, and watch your health for signs of illness.',
                                'Level 2, Moderate: Travelers at increased risk for severe illness from COVID-19 should avoid all nonessential travel.',
                                'Level 3, High: Travelers should avoid all nonessential travel',
                                'Level 4, Very High: Travelers should avoid all travel',
                              ]).astype(str)
dfya['school']= pd.cut(dfya['per100k_14daysum'],
                       bins=[-1,5,20,50,200,50000],
                       labels=['Lowest risk of transmission in schools',
                                'Lower risk of transmission in schools',
                                'Moderate risk of transmission in schools',
                                'Higher risk of transmission in schools',
                                'Highest risk of transmission in schools',
                              ]).astype(str)


display(dfya.head())

file_state_covid='USCovidStates.geojson'
gjson = state.set_index('id').join(dfya[['state','date','positive','POPESTIMATE2019','per100k_1daysum','per100k_14daysum', 'per100k_28daysum','foreign','school']].set_index('state'))
gjson.to_file(file_state_covid, driver='GeoJSON')
display(gjson.head())


# In[53]:


#Make some colorscales

# branca color names are defined in https://raw.githubusercontent.com/python-visualization/branca/master/branca/_cnames.json

colorscale = branca.colormap.linear.YlOrRd_09.scale(0, 200)
colorscale = branca.colormap.linear.YlOrRd_09.to_step(index=[0,5,20,50, 200,500, 1000])

colorscale_28 = branca.colormap.StepColormap(
    ['yellow','orange','darkorange','red','red','#440000'], 
    index=[0,5,50,100,500,3000], caption='New Cases/28days/100k (red > 100, Very High)',vmin=0, vmax=3000,
)

colorscale_28l = branca.colormap.StepColormap(
    ['yellow','orange','darkorange','red','red','#440000'], 
    index=[0,5,50,100,110,3000], caption='New Cases/28days/100k',vmin=0, vmax=3000,
).to_linear()
colorscale_28l.caption=colorscale_28.caption


colorscale_14 = branca.colormap.StepColormap(
    ['blue','green','yellow','orange','red','darkred','red','black'], 
    index=[0,5,20,50,200,201,1000,5000], caption='New Cases/14days/100k',vmin=0, vmax=400,
)

colorscale_1 = branca.colormap.StepColormap(
    ['blue','green','yellow','orange','red','red','red','black'], 
    index=[0,5,20,50,200,201,1000,5000], caption='New Cases/28days/100k',vmin=0, vmax=400,
)


display(colorscale_28)
display(colorscale_28l)




# In[54]:


# Make a map out of it:
m = folium.Map(location=[37.9, -90], zoom_start=4)


loc = """US States COVID risk per CDC <a href="https://www.cdc.gov/coronavirus/2019-ncov/travelers/map-and-travel-notices.html">Foreign Travel</a> 
      and <a href="https://www.cdc.gov/coronavirus/2019-ncov/community/schools-childcare/indicators.html#interpretation">School</a> Risk Categories</a>"""
title_html = '''
             <h3 align="center" style="font-size:16px"><b>{}</b></h3>
             <a href="https://github.com/drf5n/YCSD_covid_metrics">(source code)</a>
             '''.format(loc)   


display(gjson.columns)

def style_function_28(feature):
    y=feature['properties']['per100k_28daysum']
   # print(feature)
    return {
        'fillOpacity': 0.5,
        'weight': 0,
        'fillColor': '#black' if y is None else colorscale_28l(y)
    }

folium.GeoJson(
    file_state_covid,
    name='geojson',
    style_function=style_function_28,
    highlight_function=lambda x: {'weight': 2, 'color':'black', 'fillOpacity': 0.4,},
    tooltip=folium.features.GeoJsonTooltip(
        fields=['name',"date",'per100k_28daysum','per100k_14daysum',"POPESTIMATE2019",'foreign','school'],
        aliases=['State','Date','Cases/28d/100kpop','Cases/14d/100kpop','2019 Population','CDC Foreign Travel Rec.','CDC School'],),
    
).add_to(m)
m.add_child(colorscale_28l)
m.get_root().html.add_child(folium.Element(title_html))

#m.save('us_covid_states_map.html')
m


# In[ ]:




