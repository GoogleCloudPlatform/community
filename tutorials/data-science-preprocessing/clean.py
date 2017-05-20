"""Cleans Meteorite Landings json data.

See http://catalog.data.gov/dataset/meteorite-landings-api to download the
data this script is expecting.
"""

import argparse
import json
import re

import apache_beam
from apache_beam.io import filebasedsource


BIGQUERY_TABLE_FORMAT = re.compile(r'[\w.:-]+:\w+\.\w+$')


class JsonFileSource(filebasedsource.FileBasedSource):
    """A Beam source for JSON that emits all top-level json objects.

    Note that the beginning of a top-level json object is assumed to begin on a
    new line with no leading spaces, possibly preceded by a square bracket ([)
    or comma (,); and possibly with spaces between the bracket/comma and the
    beginning of the object.

    A custom source is necessary to enable parallelization of processing for
    the elements. The existing TextFileSource emits lines, but the Meteorite
    Landing data is a giant json array, where elements span multiple lines.
    """
    JSON_OBJECT_START = re.compile(r'^([\[,] *)?{')

    def read_records(self, file_name, offset_range_tracker):
        return self.obj_iterator(file_name, offset_range_tracker)

    @staticmethod
    def _iterable_gcs(f):
        """Create a generator for a not-quite-filelike object.

        FileBasedSource.open_file returns an object that doesn't implement the
        file interface completely, so we need this utility function in order to
        iterate over lines, while keeping the .tell() accurate.
        """
        while True:
            line = f.readline()
            if not line:
                break
            yield line

    def obj_iterator(self, file_name, offset_range_tracker):
        with self.open_file(file_name) as f:
            f.seek(offset_range_tracker.start_position() or 0)

            iterable_f = self._iterable_gcs(f)

            while True:
                current_pos = f.tell()
                # First, look for the start of an object
                # If we hit the end of the range allotted to us without finding
                # an element, stop.
                for line in iterable_f:
                    if self.JSON_OBJECT_START.match(line):
                        if not offset_range_tracker.try_claim(current_pos):
                            raise StopIteration()
                        content = [line.lstrip('[, ')]
                        break
                    current_pos = f.tell()
                else:
                    # We ran off the end of the file without finding a new
                    # object. This means we're done.
                    raise StopIteration()

                # We're in an object. Collect its contents and emit it.
                for line in iterable_f:
                    content.append(line)
                    if line.startswith('}'):
                        yield json.loads(''.join(content))
                        break
# end JsonFileSource


def discard_incomplete(record):
    """Filters out records that don't have geolocation information."""
    if 'geolocation' in record and 'year' in record:
        yield record


def convert_types(record):
    """Converts string values to their appropriate type."""
    # Only the year part of the datetime string is significant
    record['year'] = int(record['year'][:4])

    record['mass'] = float(record['mass']) if 'mass' in record else None

    geolocation = record['geolocation']
    geolocation['latitude'] = float(geolocation['latitude'])
    geolocation['longitude'] = float(geolocation['longitude'])

    return record


def filter_suspicious(record):
    """Filters records with suspicious values."""
    if record['year'] < 100:
        raise StopIteration()
    if 100 <= record['year'] < 1000:
        # Probably just forgot the leading '1'
        record['year'] += 1000

    geolocation = record['geolocation']
    if not (geolocation['latitude'] or geolocation['longitude']):
        raise StopIteration()

    yield record


def massage_rec(record):
    """Massage keys with the 'rec' prefix."""
    # These are redundant with the geolocation
    del record['reclat']
    del record['reclong']

    # Flatten the geolocation into the object
    record.update(record['geolocation'])
    del record['geolocation']
    # Probably don't need this. It seems to always be false
    del record['needs_recoding']

    # Remove the 'rec' prefix
    record['class'] = record['recclass']
    del record['recclass']  # Is it just me or is this pronounced "reckless"?

    return record


def main(src_path, dest_table, pipeline_args):
    p = apache_beam.Pipeline(argv=pipeline_args)

    value = p | 'Read JSON' >> apache_beam.Read(JsonFileSource(src_path))

    value |= (
        'Remove records that lack location or year data' >>
        apache_beam.FlatMap(discard_incomplete))

    value |= (
        'Convert string values to their types' >>
        apache_beam.Map(convert_types))

    value |= (
        'Filter bad data' >>
        apache_beam.FlatMap(filter_suspicious))

    value |= (
        'Massage fields with "rec" prefix' >>
        apache_beam.Map(massage_rec))

    value |= (
        'Dump data to BigQuery' >>
        apache_beam.Write(apache_beam.io.BigQuerySink(
            dest_table,
            schema=', '.join([
                'fall:STRING',
                'year:INTEGER',
                'nametype:STRING',
                'mass:FLOAT',
                'name:STRING',
                'class:STRING',
                'latitude:FLOAT',
                'longitude:FLOAT',
                'id:STRING',
            ]),
            create_disposition=(
                apache_beam.io.BigQueryDisposition.CREATE_IF_NEEDED),
            write_disposition=(
                apache_beam.io.BigQueryDisposition.WRITE_TRUNCATE))))

    p.run()


def bq_table(bigquery_table):
    if not BIGQUERY_TABLE_FORMAT.match(bigquery_table):
        raise argparse.ArgumentTypeError(
            'bq_table must be of format PROJECT:DATASET.TABLE')
    return bigquery_table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('src_path', help=(
        'The json file with the data. This can be either a local file, or a '
        'Google Cloud Storage uri of the form gs://bucket/object.'))
    parser.add_argument(
        'dest_table', type=bq_table, help=(
            'A BigQuery table, of the form project-id:dataset.table'))

    args, pipeline_args = parser.parse_known_args()

    main(args.src_path, args.dest_table, pipeline_args=pipeline_args)
