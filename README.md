# Querysum dataset

Code for the dataset presented in the thesis *Query-Based Abstractive Summarization Using Neural Networks* by Johan Hasselqvist and Niklas Helmertz. The code for the model can be found at a [separate repo](https://github.com/helmertz/querysum).

## Requirements

- Python 2.7 or 3.5

### NLTK

The NLTK (Natural Language Toolkit) package can be installed using `pip`:

```
pip install nltk
```

Additionally, the NLTK data package `punkt` needs to be downloaded. For installing packages, see the official guide [Installing NLTK Data](http://www.nltk.org/data.html).

## Getting CNN/Daily Mail data

The dataset for query-based abstractive summarization is created by converting an existing dataset for question answering, released by [DeepMind](https://github.com/deepmind/rc-data). Archives containing the processed DeepMind dataset can be downloaded at [http://cs.nyu.edu/~kcho/DMQA/](http://cs.nyu.edu/~kcho/DMQA/), which we used. Both the `stories` and `questions` archives are required for the conversion, from either news organization, or both. To use both, merge the extracted directories, for `questions` and `stories` separately.

## Conversion

Replacing the parts in angle brackets, the dataset can be constructed by running:

```
python convert_rcdata.py \
    <path to stories directory> \
    <path to questions directory> \
    <path to output directory>
```

This creates separate directories in the output directory for training, validation and test sets.

## Creating vocabularies

The repo contains a script for generating vocabularies, sorted by word frequency. They can be constructed by running:

```
python build_vocabularies.py \
    <path to dataset directory containing documents, queries and references> \
    <path to output directory, where document_vocabulary.txt, summary_vocabulary.txt and full_vocabulary.txt are saved>    
```