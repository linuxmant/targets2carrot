#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import pandas as pd
import yaml
from tqdm import tqdm, trange

from models import Target, Config, Library

ADDUCTS_ACETATE = ['[M+HAc-H]-', '[M+Hac-H]-']
SKIP_NAMES = ['CSH_posESI', 'CSH posESI', 'CSH_negESI', 'CSH negESI', 'unknown']


def calculate_formate(target: Target):
    """
    Creates a Formate adduct [M+FA-H]- from Acetate [M+HAc-H]- target (difference: −14.030202 Da)
    :param experiment: name of experiment for which to get the list of files

    Args:
        target:
    """

    target.name = target.name.replace('[M+HAc-H]', '[M+FA-H]').replace('[M+Hac-H]', '[M+FA-H]')
    target.accurateMass = target.accurateMass - 14.01565,

    return target


def process(params):
    if params['new']:
        process_new_format(params)
    else:
        process_lab_format(params)


def process_lab_format(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'],
                         usecols=['name', 'adduct', 'mz', 'rt(min)', 'inchikey', 'msms'])
        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for target in tbar:
            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = Target(target['name'], target['mz'], target['rt(min)'], target['msms'],
                           adduct=target['adduct'], inchikey=target['inchikey'])

                if params['formate'] and any([target['adduct'] in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{target["name"]} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(params['study'], params['instrument'], targets, params['mode'])

        library = Library(config)

        # open output file: 'application-carrot.lcms.yml'
        with open(f'{params["filename"]}.yml', 'w') as output:
            yaml.dump(library, output, explicit_start=False)

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def process_new_format(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'],
                         usecols=['index', 'name', 'retentionTime', 'retentionTimeUnit', 'accurateMass',
                                  'confirmed', 'isInternalStandard', 'requiredForCorrection', 'msms'])
        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for target in tbar:
            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = Target(target['name'], target['accurateMass'], target['retentionTime'], target['retentionTimeUnit'],
                           target['isInternalStandard'], target['requiredForCorrection'], target['confirmed'],
                           target['msms'], 0)

                if params['formate'] and any([adduct in target['name'] for adduct in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{target["index"]} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(params['study'], params['instrument'], targets, params['mode'])

        library = Library(config)

        # open output file: 'application-carrot.lcms.yml'
        with open(f'{params["filename"]}.yml', 'w') as output:
            yaml.dump(vars(library), output)

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def convert(params):
    for fileidx in trange(len(params['files'])):
        params['filename'], params['ext'] = os.path.splitext(params['files'][fileidx])
        print(params)
        try:
            tmp = params['filename'].split('/')[-1]
            params['study'], params['instrument'], params['column'], params['mode'] = tmp.split('_')
            print(params)
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
    parser.add_argument('--new', help='read input with new style', default=False, action='store_true')

    args = parser.parse_args()
    if args.files == '__unknown__':
        parser.print_help()
        SystemExit()


    def noop(self, *args, **kw):
        pass

    yaml.emitter.Emitter.process_tag = noop

    convert(vars(args))
