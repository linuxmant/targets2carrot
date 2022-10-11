#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

import pandas as pd
import yaml
from tqdm import tqdm, trange

from models import Target, Config, Library, ION_MODES

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
        df = pd.read_csv(params['filename'] + params['ext'], encoding='utf-8')
                         # usecols=['name', 'adduct', 'mz', 'rt(min)', 'inchikey', 'msms'])
        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for target in tbar:

            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = Target(name=target['name'], mz=target['mz'], rt=target['rt(min)'],
                           rt_unit='minutes', msms=target.get('msms', None),
                           adduct=target['adduct'], inchikey=target.get('inchikey', None),
                           is_istd=target.get('istd', False), tgt_type=params.get('target_type', 'istd'),
                           origin=target.get('origin', None))

                if params['formate'] and any([target['adduct'] in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{target["name"]} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(name=params['study'], instrument=params['instrument'], targets=targets, column=params['column'],
                        mode=params['mode'])

        library = Library(config)

        save_yaml(library, params['outfile'])

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def process_new_format(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'])
                         # usecols=['index', 'name', 'retentionTime', 'retentionTimeUnit', 'accurateMass',
                         #          'confirmed', 'isInternalStandard', 'requiredForCorrection', 'msms'])
        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for target in tbar:
            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = Target(name=target['name'], mz=target['accurateMass'], rt=target['retentionTime'],
                           rt_unit=target.get('retentionTimeUnit', 'minutes'), msms=target['msms'],
                           adduct=target['adduct'], inchikey=target.get('inchikey', None),
                           is_istd=target.get('istd', False), tgt_type=params.get('target_type', 'istd'),
                           origin=target.get('origin', None))

                if params['formate'] and any([adduct in target['name'] for adduct in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{target["index"]} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(params['study'], params['instrument'], targets, params['mode'])

        library = Library(config)

        save_yaml(library, params['outfile'])

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def save_yaml(library, outfile):
    with open(outfile, 'w') as output:
        yaml.dump(vars(library), output, explicit_start=False)
        print(f'file {outfile} saved...')


def convert(params):
    for fileidx in trange(len(params['files'])):
        params['filename'], params['ext'] = os.path.splitext(params['files'][fileidx])
        params['outfile'] = params.get('filename', '').replace(' ', '') + '.yml'

        try:
            tmp = params['filename'].split('/')[-1].split('-')
            params['study'], params['instrument'], params['column'] = tmp[0:3]
            params['mode'] = [k for k in ION_MODES.keys() if tmp[3] in ION_MODES[k]][0]
        except ValueError as ve:
            print(
                f'ERROR in filename: {params["filename"]}.\nIt should be <method name>-<instrument>-<column>-'
                f'<ion mode>[-<extra>].csv')

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
                        choices=['positive', 'negative'], required=False)
    parser.add_argument('-t', '--target_type', choices=['istd', 'manual'], required=False,
                        help='The type of the targets (applies to all). [\'istd\' or \'manual\']', default='istd')
    parser.add_argument('--new', help='read input with new style', default=False, action='store_true')

    args = parser.parse_args()
    if args.files == '__unknown__':
        parser.print_help()
        SystemExit()


    def noop(self, *args, **kw):
        pass


    yaml.emitter.Emitter.process_tag = noop

    convert(vars(args))
