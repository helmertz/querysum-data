from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import io
import os
import re
from os import path

pattern = re.compile('(\d+)\.(\d+)\.(.*)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_dir')
    parser.add_argument('--out_dir', default='query_offset_files')
    options = parser.parse_args()

    document_to_num_queries = {}

    for source_filename in os.listdir(options.source_dir):
        source_path = path.join(options.source_dir, source_filename)
        if path.isfile(source_path):
            document_id, _, _ = pattern.search(source_filename).groups()
            if document_id in document_to_num_queries.keys():
                document_to_num_queries[document_id] += 1
            else:
                document_to_num_queries[document_id] = 1

    if not path.isdir(options.out_dir):
        os.makedirs(options.out_dir)

    for source_filename in os.listdir(options.source_dir):
        source_path = path.join(options.source_dir, source_filename)
        if path.isfile(source_path):
            document_id, query_id, file_ending = pattern.search(source_filename).groups()
            num_queries = document_to_num_queries[document_id]
            offset_query_id = int(query_id) % num_queries + 1
            out_filepath = path.join(options.out_dir,
                                     '{}.{}.{}'.format(document_id, offset_query_id, file_ending))
            with io.open(source_path, 'r', encoding='utf-8') as source_file:
                content = source_file.read()

            with io.open(out_filepath, 'w', encoding='utf-8') as out_file:
                out_file.write(content)


if __name__ == '__main__':
    main()
