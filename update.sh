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

