import os

group_base = [
    '/project/scec_608/kmilner/ucerf3/etas_weekly/2020_05_14-weekly-1986-present-full_td-kCOV1.5',
    '/project/scec_608/kmilner/ucerf3/etas_weekly/2020_05_25-weekly-1986-present-no_ert-kCOV1.5',
    '/project/scec_608/kmilner/ucerf3/etas_weekly/2020_07_13-weekly-1986-present-gridded-kCOV1.5',
    '/project/scec_608/kmilner/ucerf3/etas_weekly/2020_07_22-weekly-1986-present-full_td'
]

for group in group_base:
    dirs_abspath = []
    basename = os.path.basename(group)
    with open(basename + '_manifest.txt', 'w') as f:
        for root, dirs, files in os.walk(group):
            for dirname in dirs:
                if dirname.startswith('Start'):
                    f.write(os.path.join(root, dirname) + '\n')

