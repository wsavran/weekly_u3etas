import os, sys

import numpy as np

from csep.core import regions
from csep.utils.constants import SECONDS_PER_WEEK
from csep.models import CatalogNumberTestResult

config = {
    'version': 2,
    'simulation_list': sys.argv[2],
    'output_dir': sys.argv[3],
    'forecast_duration_millis': SECONDS_PER_WEEK * 1000,
    'region_information': {
        'name': 'california_relm_region',
        'min_mw': 2.5,
        'max_mw': 8.0,
        'dmw': 0.1
    },
    'catalog_path': '/project/scec_608/wsavran/git/weekly_u3etas_processing/comcat-2021-02-12-unfiltered.csv',
    'job_idx': int(sys.argv[1]),
    'forecast_path': '',
    'forecast_dir': '',
}

def number_test_multiple_mag(forecast, observed_catalog, mags=[2.6, 3.0, 3.5, 4.0, 4.5, 5.0]):
    """ Performs the number test using space-magnitude binning to efficiently compute 
        number test over multiple magnitudes. 
    """
    # compute gridded event counts 
    results = []
    obs_gc = observed_catalog.spatial_magnitude_counts()
    first = True
    fore_counts = []
    for cat in forecast:
        fore_gc = cat.spatial_magnitude_counts()
        cat_counts = []
        for mag in mags:
            mag_idx = np.where(cat.region.magnitudes >= mag)[0]
            fc_count = fore_gc[:,mag_idx].sum()
            if first:
                obs_gc = fore_gc[:,mag_idx].sum()
                first = False
            cat_counts.append(fc_count)
        fore_counts.append(cat_counts)
    # prepare results
    fore_counts = np.array(fore_counts)
    for idx, mag in enumerate(mags):
        delta_1, delta_2 = get_quantiles(fore_counts[:,idx], obs_gc)
        # prepare result
        result = CatalogNumberTestResult(test_distribution=fore_counts[:,idx],
                                         name='Catalog N-Test',
                                         observed_statistic=obs_gc,
                                         quantile=(delta_1, delta_2),
                                         status='normal',
                                         obs_catalog_repr=str(observed_catalog),
                                         sim_name=forecast.name,
                                         min_mw=mag,
                                         obs_name=observed_catalog.name)
        results.append(result)
    return results
        

def create_space_magnitude_region(name, min_mw, max_mw, dmw):
    # if we include this in the package we can expand
    mapper = {'california_relm_region': regions.california_relm_region}
    region = regions.create_space_magnitude_region(
        mapper[name](),
        regions.magnitude_bins(min_mw, max_mw, dmw)
    )
    return region

def get_forecast_filepath(simulation_list, job_idx):
    with open(simulation_list) as f:
        lines = f.readlines()
    try:
        path = lines[job_idx].strip()
    except IndexError:
        print(f"No directory in manifest for index {job_idx}.")
        sys.exit(0)
    return path

def create_output_filepath(sim_dir, suffix):
    base = os.path.basename(sim_dir)
    output = '_'.join([base, suffix])
    return output
