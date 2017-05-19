"""Functions for unzipping zip archives."""

import argparse
import zipfile


def unzip(filename):
    """Generator that yields files in the given zip archive."""
    with zipfile.ZipFile(filename, 'r') as archive:
        for zipinfo in archive.infolist():
            yield archive.open(zipinfo, 'r'), {
                'name': zipinfo.filename,
            }


def main(filenames):
    for filename in filenames:
        for srcfile, metadata in unzip(filename):
            with open(metadata['name'], 'w') as f:
                f.write(srcfile.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('zip_files', nargs='+')

    args = parser.parse_args()
    main(args.zip_files)
