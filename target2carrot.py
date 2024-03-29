#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import builtins
import csv
import os
import re

import pandas as pd
import yaml
from tqdm import tqdm, trange

from models import Target, Config, Library, ION_MODES

ADDUCTS_ACETATE = ['[M+HAc-H]-', '[M+Hac-H]-']
SKIP_NAMES = ['CSH_posESI', 'CSH posESI', 'CSH_negESI', 'CSH negESI', 'unknown']
REQUIRED_COLUMNS = ['name', 'accurateMass', 'adduct', 'retentionTime', 'retentionTimeUnit', 'msms']

# backup builtin print
old_print = print


def new_print(*args, **kwargs):
    # noinspection PyBroadException
    # if tqdm.tqdm.write raises error, use builtin print
    try:
        tqdm.write(*args, **kwargs)
    except Exception as e:
        old_print(*args, **kwargs)


# globally replace print with new_print
builtins.print = new_print


def calculate_formate(target: Target):
    """
    Creates a Formate adduct [M+FA-H]- from Acetate [M+HAc-H]- target (difference: −14.030202 Da)

    Args:
        target: target to reformat
    """

    target.name = target.name.replace('[M+HAc-H]', '[M+FA-H]').replace('[M+Hac-H]', '[M+FA-H]')
    target.accurateMass = target.accurateMass - 14.01565,

    return target


def process(params):
    if params['gc']:
        process_gc_format(params)
        quit()

    if params['lab']:
        process_lab_format(params)
    else:
        process_new_format(params)


def process_gc_format(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'], encoding='utf-8')
        df.columns = df.columns.str.strip().str.lower()
        rt_col = 'rt(sec)' if 'rt(sec)' in df.columns else 'ri'
        rt_u = 'minutes' if 'rt(min)' in df.columns else 'seconds'

        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for index, target in enumerate(tbar):

            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = {'name': target['name'], 'mz': target['mz'], 'rt': target[rt_col],
                     'rt_unit': rt_u, 'ri': target['ri'], 'msms': target.get('msms', None),
                     'inchikey': target.get('inchikey', None),
                     'is_istd': target.get('istd', True),
                     'tgt_type': params.get('target_type', params.get('type', 'istd')),
                     'quant_mz': target.get('quant mz', None), 'qualifier_ion': target.get('qualifier ion', None)}

                targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{index} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(name=params['study'], instrument=params['instrument'], targets=targets, column=params['column'],
                        mode=params['mode'])

        library = Library(config)

        save_yaml(library, params['outfile'])

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"]}{params["ext"]}\n{str(err)}')
        exit(1)


def process_lab_format(params):

    try:
        df = pd.read_csv(params['filename'] + params['ext'], encoding='utf-8')
        # usecols=['name', 'adduct', 'mz', 'rt(min)', 'inchikey', 'msms'])
        df.columns = df.columns.str.strip().str.lower()
        rt_col = 'rt(min)' if 'rt(min)' in df.columns else 'ri'
        rt_u = 'minutes' if 'rt(min)' in df.columns else 'seconds'

        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for index, target in enumerate(tbar):

            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                t = Target(name=target['name'],
                           mz=target['mz'],
                           rt=target[rt_col],
                           rt_unit=rt_u,
                           msms=target.get('msms', None),
                           adduct=target.get('adduct', None),
                           inchikey=target.get('inchikey', None),
                           tgt_type=params.get('target_type', params.get('type', 'istd')))

                if params['formate'] and any([target['adduct'] in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{index} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(name=params['study'], instrument=params['instrument'], targets=targets, column=params['column'],
                        mode=params['mode'])

        library = Library(config)

        save_yaml(library, params['outfile'])

    except UnicodeDecodeError as err:
        print(
            f'Error in file {params["filename"] + params["ext"]}\n{str(err)}')
        exit(1)


def process_new_format(params):
    try:
        df = pd.read_csv(params['filename'] + params['ext'])

        # check required columns are there
        if not all([x in list(df.columns.tolist()) for x in REQUIRED_COLUMNS]):
            raise Exception(f"Missing one or more required columns.\nRequired columns are: {REQUIRED_COLUMNS}")

        targets = []
        tbar = tqdm(df.fillna('').to_dict(orient='records'))
        for index, target in enumerate(tbar):
            try:
                if any([x.lower() in target['name'].lower() for x in SKIP_NAMES]):
                    continue

                # print(target.keys())
                # print(params.keys())
                target_type = target.get('type', target.get('target_type', params.get('target_type', 'istd'))).lower()

                t = Target(name=target['name'],
                           mz=target['accurateMass'],
                           rt=target['retentionTime'],
                           rt_unit=target.get('retentionTimeUnit', 'minutes'),
                           msms=target['msms'],
                           adduct=target['adduct'],
                           inchikey=target.get('inchikey', None),
                           tgt_type=target_type)

                if params['formate'] and any([adduct in target['name'] for adduct in ADDUCTS_ACETATE]):
                    targets.append(calculate_formate(t))
                else:
                    targets.append(t)
            except UnicodeEncodeError as err:
                print(f'Error in target #{index} -- {params["filename"] + params["ext"]}')
                exit(1)

        config = Config(params['study'].replace('_', ' '), params['instrument'].replace('_', ' '), targets,
                        column=params['column'].replace('_', ' '), mode=params['mode'])

        library = Library(config)

        save_yaml(library, params['outfile'])

    except UnicodeDecodeError as err:
        print(f'Error in file {params["filename"]}{params["ext"]}\n{str(err)}')
        exit(1)


def save_yaml(library, outfile):
    with open(outfile, 'w') as output:
        yaml.dump(vars(library), output, explicit_start=False, sort_keys=False)
        print(f'file {outfile} saved...')


def convert_csv(params):
    with open(params['filename'] + params['ext'], 'r') as fin:
        data = yaml.safe_load(fin)

    lib = Library(config=data['config'][0]).config

    save_csv(lib.targets, params['outfile'])


def save_csv(targets, outfile):
    outfile = outfile.replace('.yml', '.csv').rsplit('/')[-1]
    print(f'Saving file: {outfile}')

    with open(outfile, 'w', ) as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['name', 'accurateMass', 'adduct', 'retentionTime', 'retentionTimeUnit', 'target_type',
                         'inchikey', 'confirmed', 'msms'])

        for target in targets:
            writer.writerow(target.to_csv())


def convert(params):
    for fileidx in trange(len(params['files'])):
        params['filename'], params['ext'] = os.path.splitext(params['files'][fileidx])
        params['outfile'] = params.get('filename', '').replace(' ', '') + '.yml'

        if re.match(r'\.ya?ml', params['ext']):
            print('Input file is YAML, only converting to CSV')
            try:
                convert_csv(params)
            except Exception as ex:
                message = f"{ex.__class__.__name__} {str(ex)} processing {params['filename']}{params['ext']}"
                print(message)

        else:
            print('Input file is CSV, converting to YAML')
            try:
                tmp = params['filename'].split('/')[-1].split('-')
                params['study'], params['instrument'], params['column'] = tmp[0:3]
                params['mode'] = [k for k in ION_MODES.keys() if tmp[3] in ION_MODES[k]][0]

                print(f"Method: {params['study']}, Instrument: {params['instrument']}, "
                      f"Column: {params['column']}, Ionization: {params['mode']}\n")
            except ValueError as ve:
                print(f'ERROR in filename: {params["filename"]}.\n'
                      'Spaces should be replaced with \'_\'\n'
                      f'It should be <method name>-<instrument>-<column>-<ion mode>[-<extra>].csv')

            process(params)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='list of files csv/txt with the list of targets with headers: '
                             'name, accurateMass, adduct, retentionTime, retentionTimeUnit, msms')
    parser.add_argument('--formate', help='calculates the formated adduct from an acetate adduct',
                        dest='formate', default=False, action='store_true')
    parser.add_argument('-m', '--mode', help='ion mode. [\'positive\' or \'negative\']', default='positive',
                        choices=['positive', 'negative'], required=False)
    parser.add_argument('-t', '--target_type', choices=['istd', 'manual', 'validation'], required=False,
                        help='The type of the targets (applies to all). [\'istd\' or \'manual\']', default='istd')
    parser.add_argument('--lab', help='read input with old lab random columns',
                        default=False, action='store_true')
    parser.add_argument('--gc', help='creates a gc library', action='store_true', default=False)

    args = parser.parse_args()
    if args.files == '__unknown__':
        parser.print_help()
        SystemExit()


    def noop(self, *args, **kw):
        pass


    yaml.emitter.Emitter.process_tag = noop

    convert(vars(args))
