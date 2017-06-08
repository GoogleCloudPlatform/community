import argparse
import contextlib
import os
import shutil
import tempfile

import pydub


@contextlib.contextmanager
def tempdir():
    dirname = tempfile.mkdtemp()
    yield dirname
    shutil.rmtree(dirname)


def mp3_to_raw(data, metadata):
    # Write the data to a tmpfile, for conversion
    with tempdir() as dirname:
        src = os.path.join(dirname, metadata['name'])
        dest = '{}.raw'.format(src[:src.rindex('.')])
        with open(src, 'wb') as f:
            f.write(data)
        audio = pydub.AudioSegment.from_mp3(src)
        # Convert to the format expected
        audio = audio.set_channels(1).set_sample_width(2)

        if audio.frame_rate < 8000:
            raise ValueError('Sample width must be above 8kHz')
        elif audio.frame_rate > 48000:
            audio.set_frame_rate(16000)

        audio.export(dest, format='raw')

        with open(dest, 'r') as f:
            raw_data = f.read()

    return raw_data, {
        'name': os.path.basename(dest),
        'size': len(raw_data),
        'rate': audio.frame_rate,
    }


def main(mp3_filenames):
    for mp3_filename in mp3_filenames:
        print('Converting {}'.format(mp3_filename))
        with open(mp3_filename, 'r') as f:
            raw_data, metadata = mp3_to_raw(
                f.read(), {'name': mp3_filename})
        with open(metadata['name'], 'w') as f:
            f.write(raw_data)

        print(metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('mp3_files', nargs='+')

    args = parser.parse_args()
    main(args.mp3_files)
