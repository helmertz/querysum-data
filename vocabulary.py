from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict


class Vocabulary:
    def __init__(self):
        self.word_to_count = defaultdict(int)

    def expand_vocab(self, tokens):
        for token in tokens:
            self.word_to_count[token] += 1

    def get_sorted_vocabulary(self):
        # Primarily sort by descending occurrence count and secondarily alphabetically
        return sorted(self.word_to_count.items(),
                      key=lambda word_count_tuple: (-word_count_tuple[1], word_count_tuple[0]))

    def merge(self, other_vocabulary):
        merged = Vocabulary()
        merged.word_to_count = self.word_to_count.copy()
        for word, count in other_vocabulary.word_to_count.items():
            merged.word_to_count[word] += count
        return merged
