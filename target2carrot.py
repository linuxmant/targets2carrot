#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import pandas as pd
from ruamel.yaml import YAML
from tqdm import tqdm, trange


def calculate_formate(target):
    """
    Creates a Formate adduct [M+FA-H]- from Acetate [M+HAc-H]- target (difference: −14.030202 Da)
    :param experiment: name of experiment for which to get the list of files

    Args:
        target:
    """

    target['name'] = target['name'].replace('[M+HAc-H]', '[M+FA-H]').replace('[M+Hac-H]', '[M+FA-H]')
    target['accurateMass'] = target['accurateMass'] - 14.01565,

    return target


def process(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'],
                         usecols=['index', 'name', 'retentionTime', 'retentionTimeUnit', 'accurateMass',
                                  'confirmed', 'isInternalStandard', 'requiredForCorrection', 'msms'])

        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for target in tbar:
            try:
                if any([x.lower() in target['name'].lower() for x in ['CSH_posESI', 'CSH posESI', 'CSH_negESI',
                                                                      'CSH negESI', 'unknown']]):
                    continue

                t = {'identifier': target['name'].strip(" "),
                     'accurateMass': target['accurateMass'],
                     'retentionTime': target['retentionTime'],
                     'retentionTimeUnit': target['retentionTimeUnit'],
                     'isInternalStandard': target['isInternalStandard'],
                     'requiredForCorrection': target['requiredForCorrection'],
                     'confirmed': target['confirmed'],
                     'msms': target['msms']
                     }

                if params['formate'] and any([adduct in target['name'] for adduct in ['[M+HAc-H]-', '[M+Hac-H]-']]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{target["index"]} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = [{
            'name': params['study'].split('/')[-1],
            'description': '',
            'column': params['column'],
            'ionMode': params['mode'],
            'instrument': params['instrument'],
            'minimumPeakIntensity': 10000,
            'targets': targets
        }]

        library = {'config': config}

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(sequence=4, offset=2)

        # open output file: 'application-carrot.lcms.yml'
        with open(f'{params["filename"]}.yml', 'w') as output:
            yaml.dump(library, output)

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def convert(params):
    for fileidx in trange(len(params['files'])):
        params['filename'], params['ext'] = os.path.splitext(params['files'][fileidx])
        try:
            params['study'], params['instrument'], params['column'], params['mode'] = params['filename'].split('_')
        except ValueError as ve:
            print(
                f'ERROR in filename: {params["filename"]}.\nIt should be <study name>_<instrument>_<column>_'
                f'<ion mode>.csv')

        process(params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files csv/txt with the list of targets with headers: '
                             'index, name, retentionTime, retentionTimeUnit, accurateMass,'
                             'confirmed, isInternalStandard, requiredForcorrection, msms')
    parser.add_argument('--formate', help='calculates the formated adduct from an acetate adduct',
                        dest='formate', default=False, action='store_true')
    parser.add_argument('-m', '--mode', help='ion mode. [\'positive\' or \'negative\']', default='positive',
                        choices=['positive', 'negative'])

    args = parser.parse_args()
    if args.files == '__unknown__':
        parser.print_help()
        SystemExit()

    convert(vars(args))
