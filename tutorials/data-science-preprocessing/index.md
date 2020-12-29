---
title: Cleaning data in a data processing pipeline
description: Automate the cleaning of data using Dataflow.
author: jerjou
tags: Data Science, Cloud Dataflow
date_published: 2017-05-23
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

When gathering information from the real world, the data will often contain
errors, omissions, or inconsistencies that should be corrected before you can
analyze it effectively. Instead of doing it by hand, or performing a separate
cleansing step, [Dataflow][dataflow] allows you to define simple
functions that can cleanse your data in a pipeline, which you can plug into your
data ingestion pipeline for automatic cleansing.

In this tutorial, you'll write functions to perform various data cleansing
tasks, which you'll then string together into a pipeline to be run in series on
[Dataflow][dataflow]. Note that you could also plug arbitrary functions -
such as those from the
[data extraction](/community/tutorials/data-science-extraction/) tutorial - into
this pipeline as well. We leave as an exercise for the reader.

For this example, you'll define a series of simple filters on a sample dirty
dataset. The dataset used in this tutorial is [Meteorite Landing data][meteors]
from [data.gov](https://data.gov), which catalogs, among other things, the
location and year of all known meteorite landings. You'll run the following
filters on the raw json data:

* Filtering out records without location or year filled in
* Converting the strings into their native types
* Removing redundant and bad data

You'll then tie all the filters together in a pipeline that can be run both
locally (for ease of experimentation, and for small datasets), and on the
[Dataflow][dataflow] service, for large datasets and streaming
datasets that are continuously being updated. To accomplish this, you'll add a
function for sourcing the data, and one for saving it:

* Chunk the json array into its individual elements
* Save the results in a queryable format

[dataflow]: /dataflow
[meteors]: https://catalog.data.gov/dataset/meteorite-landings-api

### Prerequisites

* You have basic familiarity with [Python][python] programming.
* You've installed [pip][pip].
* You've installed [virtualenv][virtualenv].
* You've installed the [Google Cloud SDK](/sdk).
* You've enabled the [BigQuery API][bq-api]
* For running the pipeline in the cloud, you also must enable the
  [Dataflow, Compute Engine, Cloud Logging, Cloud Storage, and Cloud Storage JSON APIs][dataflow-apis].

[setup]: /getting-started#set_up_a_project
[python]: https://www.python.org/
[pip]: https://pip.pypa.io/en/latest/installing/
[virtualenv]: http://virtualenv.pypa.io
[bq-api]: https://console.cloud.google.com/flows/enableapi?apiid=bigquery
[dataflow-apis]: https://console.cloud.google.com/flows/enableapi?apiid=dataflow,compute_component,logging,storage_component,storage_api,bigquery

## Download the tutorial data

The
[Meteorite Landings API](https://catalog.data.gov/dataset/meteorite-landings-api)
provides information in JSON format from The Meteoritical Society on all known
meteorite landings. You can download the first page of 1000 objects (according
to the [developer documentation](https://dev.socrata.com/docs/paging.html))
using the link on the landing page, or with the following:

    curl -O 'https://data.nasa.gov/resource/gh4g-9sfh.json?$limit=50000'

## Define cleansing functions

The raw data for meteorite landings contains records that don't include a
location or a year. These records are less useful because they fail to locate
the meteorite in space-time, so it might make sense to remove them. Define a
function that takes in the record, and yields it only if it has both a location
and a year defined:

[embedmd]:# (clean.py /def discard_incomplete/ /^$/)
```py
def discard_incomplete(record):
    """Filters out records that don't have geolocation information."""
    if 'geolocation' in record and 'year' in record:
        yield record
```

The records in the source dataset have values that are always strings, but if
you want to compare numerical fields as numbers, you'll need them to be
interpreted as such. Define a function that casts the relevant fields to the
appropriate types:

[embedmd]:# (clean.py /def convert_types/ /return.*/)
```py
def convert_types(record):
    """Converts string values to their appropriate type."""
    # Only the year part of the datetime string is significant
    record['year'] = int(record['year'][:4])

    record['mass'] = float(record['mass']) if 'mass' in record else None

    geolocation = record['geolocation']
    geolocation['latitude'] = float(geolocation['latitude'])
    geolocation['longitude'] = float(geolocation['longitude'])

    return record
```

After having completed the preprocessing step and gone on to explore the data,
you may notice that there are some suspicious values. For example, some entries
have the value `0.0` for both `latitude` and `longitude`. Your explorations in
the [exploratory section](/community/tutorials/data-science-exploration/) of the
process will inform the filters you'll need to clean the data up - for example,
by discarding invalid values, or making educated guesses for the correct value
when you can:

[embedmd]:# (clean.py /def filter_suspicious/ /yield.*/)
```py
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
```

Finally, clean up some redundant fields, and flatten the record in preparation
for insertion into a queryable database:

[embedmd]:# (clean.py /def massage_rec/ /return.*/)
```py
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
```

## Define a Dataflow pipeline

[Dataflow](/dataflow) uses the [Apache Beam SDK][beam]
to define a processing pipeline for the data to go through. In this case, the
data needs to be processed by each of these functions in succession and then
inserted into [BigQuery](/bigquery), after being read from its
original raw format.

### Create a `Source` for JSON objects

Apache Beam provides certain `Source` objects that can read entries from a file
and emit them one by one, but unfortunately does not provide one for json
objects. So you'll need to define one. To do this,
[the documentation][filebasedsource] says you must define a subclass of
`FileBasedSource` that implements the method `read_records`:

[embedmd]:# (clean.py /class JsonFileSource/ /^# end JsonFileSource/)
```py
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
```

This `Source` looks for the beginning of a json object by searching for a
top-level open-curly-brace (`{`), and collects all subsequent lines until it
finds a top-level close-curly-brace (`}`), whereupon it creates a json object
from the accumulated string and emits it. The result is an iterator that emits
json objects one at a time.

Note that the method makes use of a [`RangeTracker`][rangetracker] to enable
parallelization of the `Source`. That is, for large datasets, several workers
may access different ranges in the same source file to process the data in
parallel, to boost performance. The `Source`, then, is only responsible for
emitting the json objects that begin within the range assigned to it, and should
stop once it reaches the end of its range.

[beam]: http://beam.incubator.apache.org/
[filebasedsource]: /dataflow/model/custom-io-python#convenience-source-base-classes
[rangetracker]: https://beam.apache.org/documentation/sdks/python-custom-io/#implementing-the-rangetracker-subclass

### Attach the functions in series

Now that you've defined the source of data, you can pipe it through to the
filtering functions, in series. Apache Beam uses the pipe operator (`|`) to do
this (with the double angle bracket operator (`>>`) to add a description):

[embedmd]:# (clean.py /def main/ / p\.run.*/)
```py
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
```

Note that this example takes advantage of the built-in [`BigQuerySink`][bq-sink]
to output the result into BigQuery, for later analysis.

[bq-sink]: https://beam.apache.org/documentation/sdks/pydoc/2.0.0/apache_beam.io.gcp.html?highlight=bigquerysink#apache_beam.io.gcp.bigquery.BigQuerySink

## Run the data cleansing pipeline

A great thing about Apache Beam and Dataflow is that you can run it
locally for sample datasets, or datasets that are otherwise relatively small.
But then you can take the same code, add a couple extra flags, and run it using Dataflow which can handle orders of magnitude more data at a time.

You can find the complete pipeline file [here][clean.py], along with its
[requirements.txt][requirements.txt].

Because this sample uses a `BigQuerySink` for its output, you must first perform
some setup:

* First, make sure you're using the correct project:

        $ gcloud config set project your-project-id
        Updated property [core/project]
        $

* Now, create a BigQuery dataset using the `bq` command provided by the Google
  Cloud SDK:

        $ bq mk meteor_dataset
        Dataset 'your-project-id:meteor_dataset' successfully created
        $

* You should use a [virtual Python environment][h2g2-venv] to ensure that this
  example's dependencies don't conflict with any existing libraries on your
  system. The example commands below show how to set up a virtual environment
  using [virtualenv][virtualenv], though you can use another tool if you prefer.

        $ virtualenv venv
        ...
        $ source venv/bin/activate
        (venv) $ pip install -r requirements.txt
        ...
        (venv) $

With the BigQuery dataset created and your requirements installed, you are ready
to run your pipeline.

[h2g2-venv]: http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/
[clean.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-preprocessing/clean.py
[requirements.txt]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-preprocessing/requirements.txt

### Running locally

To run your preprocessing pipeline on your computer, simply run your script like
so:

    python clean.py meteors.json your-project-id:meteor_dataset.cleansed

### Running on Dataflow

To run the script on Dataflow, you'll have to specify your project, and a
bucket in Cloud Storage:

    PROJECT=your-project-id
    # The $PROJECT.appspot.com bucket is created automatically with your project
    BUCKET=gs://$PROJECT.appspot.com

Now upload the json data file to Cloud Storage using the `gsutil` tool included
in the Cloud SDK:

    gsutil cp meteors.json gs://$BUCKET/

Then run:

    python clean.py gs://$BUCKET/meteors.json $PROJECT:meteor_dataset.cleansed \
        --project $PROJECT \
        --job_name $PROJECT-meteors \
        --runner BlockingDataflowPipelineRunner \
        --staging_location $BUCKET/staging \
        --temp_location $BUCKET/temp \
        --output $BUCKET/output

You can check the status of your job on the
[Dataflow dashboard](https://console.cloud.google.com/dataflow?project=_).

## Sample query

Now that the data has been ingested into BigQuery, it's available to explore.
We'll go into more detail about this in the next section on
[data exploration](/community/tutorials/data-science-exploration/), but to give
you an idea, here is a sample query we could do to find the number of meteor
landings per year:

     $ bq query "select year, count(*) from \
         [$PROJECT:meteor_dataset.cleansed] \
         group by year \
         order by year desc \
         limit 10"
     Waiting on bqjob_r2a3ebeea2f95498c_00000158939ae926_1 ... (0s) Current
     status: DONE
     +------+------+
     | year | f0_  |
     +------+------+
     | 2013 |    1 |
     | 2012 |   15 |
     | 2011 |  391 |
     | 2010 |  420 |
     | 2009 |  323 |
     | 2008 |  261 |
     | 2007 |  236 |
     | 2006 | 1223 |
     | 2005 |  246 |
     | 2004 |  264 |
     +------+------+

## API Documentation

We've only touched on a couple of the capabilities of Apache Beam and
Dataflow. Take a look at the API documentation, and experiment with the other
features.

* Cloud Dataflow ([API Docs](/dataflow/docs))
* Apache Beam ([Project page][beam] | [Python Docs][beam-py] | [Java Docs][beam-java])

[beam-py]: https://beam.apache.org/documentation/sdks/pydoc/2.0.0/
[beam]: http://beam.incubator.apache.org/
[beam-java]: http://beam.incubator.apache.org/documentation/programming-guide/

## Cleanup

To avoid recurring charges for resources created in this tutorial:

* Delete the BigQuery table that you used for your data output. **Note**,
  though, that this table will be used in subsequent tutorials in this series,
  so you might want to hold off on this until you've gone through the
  [next tutorial](/community/tutorials/data-science-exploration/):

        $ bq rm -r meteor_dataset
        rm: remove dataset 'your-project-id:meteor_dataset'? (y/N) y

* Delete the objects created in Cloud Storage when running the script on
  Dataflow:

        gsutil rm -r gs://$BUCKET/staging gs://$BUCKET/temp gs://$BUCKET/output \
            gs://$BUCKET/meteors.json
