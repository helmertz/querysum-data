from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import io
import os
import sys

from vocabulary import Vocabulary


class Vocabularies:
    def __init__(self):
        self.document_vocabulary = Vocabulary()
        self.summary_vocabulary = Vocabulary()
        self.full_vocabulary = Vocabulary()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    options = parser.parse_args()

    print("Counting words...")
    sys.stdout.flush()
    vocabularies = extract_vocabularies(options)
    print("Done")

    print("Saving to output directory...")
    sys.stdout.flush()
    write_vocabularies(options, vocabularies)
    print("Done")


def extract_vocabularies(options):
    vocabularies = Vocabularies()

    document_vocabulary = extract_vocabulary(options, 'documents')
    summary_vocabulary = extract_vocabulary(options, 'references')

    vocabularies.document_vocabulary = document_vocabulary
    vocabularies.summary_vocabulary = summary_vocabulary
    vocabularies.full_vocabulary = document_vocabulary.merge(summary_vocabulary)

    return vocabularies


def extract_vocabulary(options, dir_name):
    vocabulary = Vocabulary()

    dir_path = os.path.join(options.input_dir, dir_name)
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            with io.open(file_path, 'r', encoding='utf-8') as file:
                raw_text = file.read()
                vocabulary.expand_vocab(raw_text.split())
    return vocabulary


def write_vocabularies(options, vocabularies):
    # Write all three types of vocabulary to file
    for vocabulary_name, vocabulary in vocabularies.__dict__.items():
        write_vocabulary(options, '{}.txt'.format(vocabulary_name), vocabulary)


def write_vocabulary(options, name, vocabulary):
    sorted_vocabulary = vocabulary.get_sorted_vocabulary()
    with io.open(os.path.join(options.output_dir, name), 'w', encoding='utf-8') as file:
        for word, count in sorted_vocabulary:
            file.write('{} {}\n'.format(word, count))


if __name__ == '__main__':
    main()
