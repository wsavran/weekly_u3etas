import os
import sys
import json
import time

import numpy as np

from csep import load_catalog_forecast, load_catalog, write_json
from csep.core import regions, catalog_evaluations
from csep.utils.constants import SECONDS_PER_WEEK
from csep.utils.file import mkdirs
from csep.utils.stats import get_quantiles
from csep.models import CatalogNumberTestResult

config = {
    'version': 2,
    'simulation_list': sys.argv[2],
    'output_dir': sys.argv[3],
    'forecast_duration_millis': SECONDS_PER_WEEK * 1000,
    'region_information': {
        'name': 'california_relm_region',
        'min_mw': 2.6,
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

def process_ucerf3_forecast(config):
    """ Post-processing script for ucerf3-forecasts

    Program will perform N, M, and S tests and write out evaluation results.

    Args:
        config (dict): contents of configuration needed to run the job

    """
    # Get directory of forecast file from simulation manifest
    forecast_dir = get_forecast_filepath(config['simulation_list'], config['job_idx'])
    config.update({'forecast_dir': forecast_dir})
    print(f"Working on forecast in {config['forecast_dir']}.")

    # Search for forecast files
    forecast_path = os.path.join(forecast_dir, 'results_complete.bin.gz')
    if not os.path.exists(forecast_path):
        print(f"Did not find a forecast at {forecast_path}. Looking for uncompressed version.", flush=True)
        forecast_path = os.path.join(forecast_dir, 'results_complete.bin')
        if not os.path.exists(forecast_path):
            print(f"Unable to find uncompressed forecast. Aborting.", flush=True)
            sys.exit(-1)
    config['forecast_path'] = forecast_path
    print(f"Found forecast file at {config['forecast_path']}.")

    # Create output directory
    mkdirs(config['output_dir'])

    # Initialize processing tasks
    print(f"Processing forecast at {forecast_path}.", flush=True)
    config_path = os.path.join(config['forecast_dir'], 'config.json')
    with open(config_path) as json_file:
        u3etas_config = json.load(json_file)

    # Time horizon of the forecast
    start_epoch = u3etas_config['startTimeMillis']
    end_epoch = start_epoch + config['forecast_duration_millis']
    config['start_epoch'] = start_epoch
    config['end_epoch'] = end_epoch

    # Create region information from configuration file
    region_config = config['region_information']
    region = create_space_magnitude_region(
        region_config['name'],
        region_config['min_mw'],
        region_config['max_mw'],
        region_config['dmw']
    )
    min_magnitude = region.magnitudes[0]

    # Set up filters for forecast and catalogs
    filters = [f'origin_time >= {start_epoch}',
               f'origin_time < {end_epoch}',
               f'magnitude >= {min_magnitude}']

    # Forecast, note: filters are applied when iterating through the forecast
    forecast_basename = os.path.basename(config['forecast_dir'])
    forecast = load_catalog_forecast(forecast_path,
                                     type='ucerf3',
                                     name=f'ucerf3-{forecast_basename}',
                                     region=region,
                                     filters=filters,
                                     filter_spatial=True,
                                     apply_filters=True)

    # Sanity check to ensure that forecasts are filtered properly
    min_mws = []
    for catalog in forecast:
        if catalog.event_count > 0:
            min_mws.append(catalog.get_magnitudes().min())
    print(f"Overall minimum magnitude of catalogs in forecast: {np.min(min_mws)}")
        
    # Compute expected rates for spatial test and magnitude test
    _ = forecast.get_expected_rates()
    sc = forecast.expected_rates.spatial_counts()
    sc_path = os.path.join(
        config['output_dir'],
        create_output_filepath(config['forecast_dir'], 'spatial_counts_arr-f8.bin')
    )
    with open(sc_path, 'wb') as sc_file:
        print(f"Writing spatial counts to {sc_path}")
        sc.tofile(sc_file)

    # Prepare evaluation catalog
    eval_catalog = load_catalog(config['catalog_path'],
                                region=region,
                                filters=filters,
                                name='comcat',
                                apply_filters=True)

    # Compute and store number test
    print("Computing number-test on forecast.")
    ntest_result = catalog_evaluations.number_test(forecast, eval_catalog)
    ntest_path = os.path.join(
        config['output_dir'],
        create_output_filepath(config['forecast_dir'], 'ntest_result.json')
    )
    try:
        write_json(ntest_result, ntest_path)
        config['ntest_path'] = ntest_path
        print(f"Writing outputs to {config['ntest_path']}.")
    except IOError:
        print("Unable to write n-test result.")

    # Compute number test over multiple magnitudes
    print("Computing number test over multiple magnitudes")
    ntest_results = number_test_multiple_mag(forecast, eval_catalog)
    config['ntest_paths'] = []
    for r in ntest_results:
        min_mw = r.min_mw
        ntest_path = os.path.join(
            config['output_dir'],
            create_output_filepath(config['forecast_dir'], 'ntest_result_' + str(min_mw).replace('.','p') + '.json')
        )
        try:
            write_json(ntest_result, ntest_path)
            config['ntest_paths'].append(ntest_path)
            print(f"Writing outputs to {ntest_path}.")
        except IOError:
            print("Unable to write n-test result.")


    # Compute and store magnitude test
    print("Computing magnitude-test on forecast.")
    mtest_result = catalog_evaluations.magnitude_test(forecast, eval_catalog)
    mtest_path = os.path.join(
            config['output_dir'],
            create_output_filepath(config['forecast_dir'], 'mtest_result.json')
    )
    try:
        write_json(mtest_result, mtest_path)
        config['mtest_path'] = mtest_path
        print(f"Writing outputs to {config['mtest_path']}.")
    except IOError:
        print("Unable to write m-test result.")

    # Compute and store spatial test
    print("Computing spatial test on forecast.")
    stest_path = os.path.join(
        config['output_dir'],
        create_output_filepath(config['forecast_dir'], 'stest_result.json')
    )
    stest_result = catalog_evaluations.spatial_test(forecast, eval_catalog)
    try:
        write_json(stest_result, stest_path)
        config['stest_path'] = stest_path
    except (IOError, TypeError, ValueError):
        print("Unable to write s-test result.")

    # Write calculation configuration
    config_path = os.path.join(
        config['output_dir'],
        create_output_filepath(config['forecast_dir'], 'meta.json')
    )
    print(f"Saving run-time configuration to {config_path}.")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    t0 = time.time()
    process_ucerf3_forecast(config)
    t1 = time.time()
    print(f"Finished processing forecast in {t1 - t0:.2f} seconds.")
