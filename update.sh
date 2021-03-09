#!/bin/bash

IPY=/Users/drf/anaconda3/envs/py3plot/bin/ipython

for file in *.ipynb; do 

if [ "$file" -nt "${file%.ipynb}.py" ] ; then 
# Save notebook as a python script:
jupyter nbconvert --to script $file
fi

done

$IPY CovidStates.py 
$IPY YorkCountyCovidMetric.py 
$IPY AllCountyCovidMetric.py 


$IPY <<EOT

import os,glob
import time
from selenium import webdriver

delay=5

def html_to_png(fn):
    #Save the map as an HTML file
    #fn='docs/us_covid_states_map.html'
    #fn.replace('html','png')
    tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
    fn_png = fn.replace('.html','.png')
    browser.get(tmpurl)
    time.sleep(delay)
    browser.save_screenshot(fn.replace('.html','.png'))

options = webdriver.ChromeOptions()
options.headless = True
browser = webdriver.Chrome('/usr/local/bin/chromedriver',options=options)
for fn in glob.glob('docs/*map*.html'):
    html_to_png(fn)
browser.quit()



EOT

echo "Commit & push will update https://github.com/drf5n/YCSD_covid_metrics/"
