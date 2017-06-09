from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
from os import path

from pyrouge import Rouge155


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('system_dir')
    parser.add_argument('reference_dir')
    parser.add_argument('rouge_dir')
    options = parser.parse_args()

    rouge_score = compute_rouge(options)
    print(rouge_score)


def compute_rouge(options):
    system_dir = options.system_dir
    reference_dir = options.reference_dir

    rouge_data = path.join(options.rouge_dir, 'data')
    rouge_args = '-e {} -c 95 -2 4 -U -n 4 -w 1.2 -a'.format(rouge_data)

    rouge = Rouge155(rouge_dir=options.rouge_dir, rouge_args=rouge_args)
    rouge.system_dir = system_dir
    rouge.model_dir = reference_dir
    rouge.system_filename_pattern = '(\d+.\d+).txt'
    rouge.model_filename_pattern = '[A-Z].#ID#.txt'

    return rouge.convert_and_evaluate()


if __name__ == '__main__':
    main()
