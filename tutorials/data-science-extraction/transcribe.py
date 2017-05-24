import argparse
import logging
import random
import time

from google.cloud import speech


def Error(Exception):
    """Module-level error superclass."""


def TranscriptionError(Error):
    pass


def _poll(operation, upper_bounds):
    n = 0
    while not operation.complete:
        sleep_secs = random.triangular(
            1, 1 + upper_bounds,
            1 + (.99**n) * upper_bounds)
        n += 1

        logging.debug('Sleeping for %s', sleep_secs)
        time.sleep(sleep_secs)

        operation.poll()
        logging.debug(operation)

    return operation


def transcribe(bucket, path, metadata):
    client = speech.Client()

    sample = client.sample(source_uri='gs://{}/{}'.format(bucket, path),
                           encoding=speech.Encoding.LINEAR16,
                           sample_rate_hertz=metadata['rate'])
    operation = sample.long_running_recognize(
        language_code='en-US',
        max_alternatives=1,
    )
    file_size_megs = metadata['size'] * 2**-20
    operation = _poll(operation, file_size_megs)

    if operation.error:
        logging.error('Error transcribing gs://{}/{}: {}'.format(
            bucket, path, operation.error))
        raise TranscriptionError(operation.error)
    else:
        best_transcriptions = [r.alternatives[0] for r in operation.results
                               if r.alternatives]
        return best_transcriptions, metadata


def main(uris, rate, size):
    for uri in uris:
        logging.info('Transcribing {}'.format(uri))

        bucket, path = uri[5:].split('/', 1)
        transcriptions, metadata = transcribe(bucket, path, {
            'size': size,
            'rate': rate,
        })
        for t in transcriptions:
            print('({}): {}\n'.format(t.confidence, t.transcript))


def _gcs_uri(text):
    if not text.startswith('gs://'):
        raise argparse.ArgumentTypeError(
            'Must be a uri of the form gs://bucket/object')
    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('gcs_uris', nargs='+', type=_gcs_uri)
    parser.add_argument('--rate', type=int, required=True)
    parser.add_argument('--size', type=int, required=True)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    main(args.gcs_uris, args.rate, args.size)
