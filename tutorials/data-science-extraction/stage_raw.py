import argparse

from google.cloud import storage


# TODO: set this as a parameter to the dataflow job? side-input?
DESTINATION_BUCKET = 'data-science-getting-started'


def stage_audio(data, metadata, destination_bucket=DESTINATION_BUCKET):
    client = storage.Client()
    blob = client.bucket(destination_bucket).blob(metadata['name'])
    blob.upload_from_string(data, content_type='application/octet-stream')

    return destination_bucket, metadata['name'], metadata


def main(audio_files, destination_bucket):
    for filename in audio_files:
        print('Uploading {}'.format(filename))
        with open(filename, 'rb') as f:
            print(stage_audio(
                f.read(), {'name': filename}, destination_bucket))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('audio_files', nargs='+')
    parser.add_argument('--bucket', required=True)

    args = parser.parse_args()
    main(args.audio_files, args.bucket)
