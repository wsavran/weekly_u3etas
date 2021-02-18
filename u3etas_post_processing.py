import os
import sys
import json
import time

from csep import load_catalog_forecast, load_catalog, write_json
from csep.core import regions, catalog_evaluations
from csep.utils.constants import SECONDS_PER_WEEK
from csep.utils.file import mkdirs

config = {
    'simulation_list': '/home1/wsavran/scratch/2020_05_14-weekly-1986-present-full_td-kCOV1.5_manifest.txt',
    'output_dir': '/project/scec_608/wsavran/csep/u3etas_weekly/2020_05_14-weekly-1986-present-full_td-kCOV1.5',
    'forecast_duration_millis': SECONDS_PER_WEEK * 1000,
    'region_information': {
        'name': 'california_relm_region',
        'min_mw': 2.95,
        'max_mw': 8.0,
        'dmw': 0.2
    },
    'catalog_path': '/project/scec_608/wsavran/git/weekly_u3etas_processing/comcat-2021-02-12-unfiltered.csv',
    'job_idx': int(sys.argv[1]),
    'forecast_path': '',
    'forecast_dir': '',
}

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
    return lines[job_idx].strip()

def create_output_filepath(sim_dir, suffix):
    base = os.path.basename(sim_dir)
    output = '_'.join([base, suffix])
    return output

def process_ucerf3_forecast(config):
    """ Post-processing script for ucerf3-forecasts

    Program will perform N and S tests and write out evaluation results.

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

    # Compute expected rates for spatial test
    _ = forecast.get_expected_rates()

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
    write_json(ntest_result, ntest_path)
    config['ntest_path'] = ntest_path
    print(f"Writing outputs to {config['ntest_path']}.")

    # Compute and store spatial test
    print("Computing spatial test on forecast.")
    stest_path = os.path.join(
        config['output_dir'],
        create_output_filepath(config['forecast_dir'], 'stest_result.json')
    )
    stest_result = catalog_evaluations.spatial_test(forecast, eval_catalog)
    write_json(stest_result, stest_path)
    config['stest_path'] = stest_path

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
