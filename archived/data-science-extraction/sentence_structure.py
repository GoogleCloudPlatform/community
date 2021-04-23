import argparse
import fileinput
import logging
import sys

from google.cloud import language


def _get_native_encoding_type():
    """Returns the encoding type that matches Python's native strings."""
    if sys.maxunicode == 65535:
        return language.Encoding.UTF16
    else:
        return language.Encoding.UTF32


def extract_syntax(transcriptions, metadata):
    """Extracts tokens in transcriptions using the GCP Natural Language API."""
    client = language.Client()

    document = client.document_from_text(
            '\n'.join(transcriptions), language='en',
            encoding=_get_native_encoding_type())
    # Only extracting tokens here, but the API also provides these other things
    sentences, tokens, sentiment, entities, lang = document.annotate_text(
            include_syntax=True, include_entities=False,
            include_sentiment=False)

    return tokens, metadata


def main(input_files):
    for line in fileinput.input(input_files):
        logging.info('Analyzing "{}"'.format(line))

        tokens, metadata = extract_syntax([line], {})
        for token in tokens:
            print('{}: {}'.format(token.text_content, token.part_of_speech))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('input_files', nargs='+', default='-')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    main(args.input_files)
