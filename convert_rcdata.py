from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import hashlib
import io
import math
import os
import re
import shutil
import sys

import nltk


class ArticleData:
    def __init__(self, article_text=None, query_to_summaries=None, entities=None):
        self.article_text = article_text
        if query_to_summaries is None:
            self.query_to_summaries = {}
        else:
            self.query_to_summaries = query_to_summaries
        self.entities = entities


class Summaries:
    def __init__(self, first_query_sentence=None, reference_summaries=None, synthetic_summary=None):
        self.first_query_sentence = first_query_sentence
        self.reference_summaries = reference_summaries
        self.synthetic_summary = synthetic_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stories_dir')
    parser.add_argument('questions_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--validation_test_fraction', type=float, default=0.015)
    parser.add_argument('--save_first_query_sentences', action='store_true')
    parser.add_argument('--save_document_lengths', action='store_true')
    parser.add_argument('--save_synthetic_references', action='store_true')
    options = parser.parse_args()

    print("Extracting summarization data...")
    sys.stdout.flush()
    article_lookup = extract_article_lookup(options)
    print("Done")

    print("Saving to output directory...")
    sys.stdout.flush()
    write_data(article_lookup, options)
    print("Done")


def extract_article_lookup(options):
    # Initialize dictionary to contain both reference summaries and the first query sentence
    article_lookup = {}

    # Look through all question files
    num_processed_items = 0
    for root, dirs, files in os.walk(options.questions_dir):
        for question_file_name in files:
            if not question_file_name.endswith('.question'):
                continue
            with io.open(os.path.join(root, question_file_name), 'r', encoding='utf-8') as question_file:
                question_text = question_file.read()
            url, query, entities = extract_from_question(question_text)

            article_data = article_lookup.get(url)

            if article_data is None:
                # First time article is processed
                article_data = ArticleData(entities=entities)
                article_lookup[url] = article_data

            # Check if summaries for the document-query pair has already been found
            summaries = article_data.query_to_summaries.get(join(query))
            if summaries is not None:
                continue

            extract_from_story(query, article_data, options.stories_dir, url)

            # Print progress
            num_processed_items += 1
            if num_processed_items % 1000 == 0:
                print('{} items processed...'.format(num_processed_items))
    return article_lookup


def extract_from_question(question_text):
    lines = question_text.splitlines()

    url = lines[0]
    placeholder = lines[6]
    entity_mapping_lines = lines[8:]

    entity_dictionary = get_entity_dictionary(entity_mapping_lines)

    query = entity_dictionary[placeholder]
    tokenized_query = tokenize(query)
    entities = '\n'.join([join(tokenize(entity)) for entity in entity_dictionary.values()])

    return url, tokenized_query, entities


def get_entity_dictionary(entity_mapping_lines):
    entity_dictionary = {}
    for mapping in entity_mapping_lines:
        entity, name = mapping.split(':', 1)
        entity_dictionary[entity] = name
    return entity_dictionary


def generate_synthetic_summary(document, highlight):
    return [word for word in highlight if word in document]


def extract_from_story(query, article_data, stories_path, url):
    # Find original story file which is named using the URL hash
    url_hash = hash_hex(url)
    with io.open(os.path.join(stories_path, '{}.story'.format(url_hash)), 'r', encoding='utf-8') as file:
        raw_article_text = file.read()

    highlight_start_index = raw_article_text.find('@highlight')

    article_text = raw_article_text[:highlight_start_index].strip()
    highlight_text = raw_article_text[highlight_start_index:].strip()

    if len(article_text) == 0:
        # There are stories with only highlights, skip these
        return

    # Extract all highlights
    highlights = re.findall('@highlight\n\n(.*)', highlight_text)

    tokenized_highlights = map(tokenize, highlights)
    tokenized_query_highlights = []

    for highlight in tokenized_highlights:
        if contains_sublist(highlight, query):
            tokenized_query_highlights.append(highlight)

    if len(tokenized_query_highlights) == 0:
        # For now, ignore if sequence of tokens not found in any highlight. It happens for example when query is
        # "American" and highlight contains "Asian-American".
        return

    first_query_sentence = get_first_query_sentence(query, article_text)

    synthetic_summary = generate_synthetic_summary(first_query_sentence, tokenized_query_highlights[0])

    summaries = Summaries(join(first_query_sentence), map(join, tokenized_query_highlights), join(synthetic_summary))

    if article_data.article_text is None:
        article_data.article_text = join(tokenize(article_text))

    article_data.query_to_summaries[join(query)] = summaries


def contains_sublist(list_, sublist):
    for i in range(len(list_)):
        if list_[i:(i + len(sublist))] == sublist:
            return True
    return False


def get_first_query_sentence(query, text):
    # Find sentence containing the placeholder
    sentences = []
    for paragraph in text.splitlines():
        sentences.extend(nltk.sent_tokenize(paragraph))

    for sentence in sentences:
        tokenized_sentence = tokenize(sentence)
        if contains_sublist(tokenized_sentence, query):
            first_query_sentence = tokenized_sentence
            break
    else:
        # Query text not found in document, pick first sentence instead
        first_query_sentence = sentences[0]

    # If ending with a period, remove it, to match most of the highlights
    # (some are however single sentences ending with period)
    if first_query_sentence[-1] == '.':
        first_query_sentence = first_query_sentence[:-1]

    return first_query_sentence


apostrophe_words = {
    "''",
    "'s",
    "'re",
    "'ve",
    "'m",
    "'ll",
    "'d",
    "'em",
    "'n'",
    "'n",
    "'cause",
    "'til",
    "'twas",
    "'till"
}


def lower_and_fix_apostrophe_words(word):
    regex = re.compile("^'\D|'\d+[^s]$")  # 'g | not '90s
    word = word.lower()

    if regex.match(word) and word not in apostrophe_words:
        word = "' " + word[1:]
    return word


def tokenize(text):
    # The Stanford tokenizer may be preferable since it was used for pre-trained GloVe embeddings. However, it appears
    # to be unreasonably slow through the NLTK wrapper.

    tokenized = nltk.tokenize.word_tokenize(text)
    tokenized = [lower_and_fix_apostrophe_words(word) for word in tokenized]
    return tokenized


def join(text):
    return " ".join(text)


def hash_hex(string):
    hash_ = hashlib.sha1()
    hash_.update(string.encode('utf-8'))
    return hash_.hexdigest()


def write_data(articles, options):
    output_dir = options.output_dir

    shutil.rmtree(output_dir, True)

    total_reference_count = 0

    # Ignore articles where no query was found
    filtered_articles = [item for item in articles.items() if len(item[1].query_to_summaries) > 0]

    # Get articles ordered by hash values to break possible patterns in ordering
    sorted_articles = sorted(filtered_articles, key=lambda article_tuple: hash_hex(article_tuple[0]))

    num_validation_test_documents = math.ceil(options.validation_test_fraction * len(sorted_articles))

    validation_articles = sorted_articles[:num_validation_test_documents]
    test_articles = sorted_articles[num_validation_test_documents:(2 * num_validation_test_documents)]
    training_articles = sorted_articles[(2 * num_validation_test_documents):]
    out_sets = [('validation', validation_articles),
                ('test', test_articles),
                ('training', training_articles)]

    for set_name, articles in out_sets:
        output_set_dir = os.path.join(output_dir, set_name)

        out_names = ['queries', 'documents', 'references', 'entities']

        if options.save_first_query_sentences:
            out_names.append('first_query_sentences')
        if options.save_synthetic_references:
            out_names.append('synthetic_references')

        out_paths = [os.path.join(output_set_dir, x) for x in out_names]
        out_name_to_path = dict(zip(out_names, out_paths))

        for out_path in out_paths:
            os.makedirs(out_path)

        document_id = 1
        reference_num_tokens_lines = []

        for url, article_data in articles:
            query_to_summaries = article_data.query_to_summaries

            # Ignore if no queries were found for article
            if len(query_to_summaries) == 0:
                continue

            article_dir_content_mapping = [(out_name_to_path['documents'], article_data.article_text),
                                           (out_name_to_path['entities'], article_data.entities)]

            document_filename = '{}.txt'.format(document_id)

            for dir_, content in article_dir_content_mapping:
                with io.open(os.path.join(dir_, document_filename), 'w', encoding='utf-8') as file:
                    file.write(content)

            query_id = 1
            for query, summaries in sorted(query_to_summaries.items(),
                                           key=lambda query_tuple: hash_hex(query_tuple[0])):
                query_filename = '{}.{}.txt'.format(document_id, query_id)

                dir_content_mapping = [(out_name_to_path['queries'], query)]
                if options.save_first_query_sentences:
                    dir_content_mapping.append(
                        (out_name_to_path['first_query_sentences'], summaries.first_query_sentence))

                for dir_, content in dir_content_mapping:
                    with io.open(os.path.join(dir_, query_filename), 'w', encoding='utf-8') as file:
                        file.write(content)

                if options.save_synthetic_references:
                    synthetic_filename = 'A.{}.{}.txt'.format(document_id, query_id)
                    with io.open(os.path.join(out_name_to_path['synthetic_references'], synthetic_filename), 'w',
                                 encoding='utf-8') as file:
                        file.write(summaries.synthetic_summary)

                # Save reference summaries
                reference_id = 0
                for reference_summary in sorted(summaries.reference_summaries, key=hash_hex):
                    reference_filename = '{}.{}.{}.txt'.format(chr(ord('A') + reference_id), document_id, query_id)
                    with io.open(
                            os.path.join(out_name_to_path['references'], reference_filename),
                            'w',
                            encoding='utf-8') as file:
                        file.write(reference_summary)
                    num_tokens_line = '{} {}'.format(reference_filename, len(article_data.article_text.split()))
                    reference_num_tokens_lines.append(num_tokens_line)

                    reference_id += 1
                    total_reference_count += 1

                    # Print progress
                    if total_reference_count % 1000 == 0:
                        print('{} items processed...'.format(total_reference_count))
                query_id += 1
            document_id += 1

        if options.save_document_lengths:
            with io.open(os.path.join(output_set_dir, 'input_lengths.txt'), 'w', encoding='utf-8') as file:
                for line in reference_num_tokens_lines:
                    file.write(line)
                    file.write('\n')


if __name__ == '__main__':
    main()
