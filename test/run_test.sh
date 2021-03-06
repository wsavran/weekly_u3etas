#! /bin/bash

echo "Running test simulation for /project/scec_608/wsavran/csep/u3etas_weekly/2020_07_22-weekly-1986-present-full_td/Start2011_08_17_ntest_result.json"
python ../u3etas_post_processing.py 0 ../full_td/2020_07_22-weekly-1986-present-full_td_manifest.txt /project/scec_608/wsavran/git/weekly_u3etas_processing/manual_testing

echo "Checking output from this run against stored results"
if ! cmp Start2011_08_17_ntest_result.json /project/scec_608/wsavran/csep/u3etas_weekly/2020_07_22-weekly-1986-present-full_td/Start2011_08_17_ntest_result.json 
then
    echo "Warning: Results differ for n-test you should re-compute the simulation results"
else
    echo "n-test results match."
fi
if ! cmp Start2011_08_17_stest_result.json /project/scec_608/wsavran/csep/u3etas_weekly/2020_07_22-weekly-1986-present-full_td/Start2011_08_17_stest_result.json 
then
    echo "Warning: Results differ for s-test you should re-compute the simulation results"
else
    echo "s-test results match."
fi
