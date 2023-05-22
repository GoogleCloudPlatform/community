---
title: Data extraction from audio and text
description: Extract structured data from audio and text.
author: jerjou
tags: Data Science
date_published: 2017-05-23
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Oftentimes, the raw data you've gathered is not in a form that is directly
explorable using the data exploration tools at your disposal. Making it usable
may require converting the format, extracting the information type you're
seeking, or adding metadata to further structure the data.

Google Cloud makes it easy to write specialized functions to transform
your data and chain them into a
[pipeline](/community/tutorials/data-science-preprocessing/), and provides a
number of Machine Learning APIs that enable you to [transcribe audio][speech];
[identify faces, landmarks, and text][vision] in images; [translate][translate]
between languages; and [provide structure to prose][natural-language].

In this tutorial, you'll write several functions to perform various
transformations and extraction to turn raw audio files into structured,
queryable data. These functions can then be easily combined together into a
reusable data ingestion pipeline, as described in the
[preprocessing](/community/tutorials/data-science-preprocessing/) tutorial.

[speech]: /speech
[vision]: /vision
[translate]: /translate
[natural-language]: /natural-language

### Objectives

This data extraction pipeline example can be described as a series of discrete
steps:

* Unzipping a collection of `mp3` audio files
* Converting the `mp3`s to raw `LINEAR16` audio
* Uploading the raw audio files to Google Cloud Storage
* Extract transcription of speech from the audio files
* Process the transcription to identify the entities.
* Save the results

### Prerequisites

* You've enabled the [Cloud Speech API][speech-api] and the
  [Cloud Natural Language API][nl-api] in your Cloud Console project.
* You've downloaded [service account credentials][service-account] and set the
  `GOOGLE_APPLICATION_DEFAULT` environment variable to point to them.
  ([More details][auth])
* You have basic familiarity with [Python][python] programming.
* You've installed [pip][pip].
* You've installed [virtualenv][virtualenv]

[speech-api]: https://console.cloud.google.com/apis/api/speech.googleapis.com/overview?project=_
[nl-api]: https://console.cloud.google.com/apis/api/language.googleapis.com/overview?project=_
[service-account]: https://console.cloud.google.com/apis/credentials?project=_
[python]: https://www.python.org/
[pip]: https://pip.pypa.io/en/latest/installing/
[virtualenv]: http://virtualenv.pypa.io
[auth]: /docs/authentication#developer_workflow

## Download the tutorial data

For this tutorial, we'll extract data from readings of Aesop's Fables from
[LibriVox](//librivox.org/author/181) for demonstration purposes. For
convenience, we've cached a copy of the zip files in a
[Cloud Storage][storage] bucket:

* [Download][aesop1.zip] the first audio file, to use while writing and testing
  your preprocessing functions.
* You can also browse the whole collection of audio files [here][librivox-archives].

[aesop1.zip]: https://archive.org/download/aesop_fables_volume_one_librivox/aesop_fables_volume_one_librivox_64kb_mp3.zip
[librivox-archives]: https://archive.org/download/aesop_fables_volume_one_librivox
[storage]: /storage

## Convert the file

The file as downloaded from LibriVox is in a zip archive, which we'll need to
convert into a format that the API accepts. In order to do this, we'll first
define a function that unzips the archive, producing each file successively:

[embedmd]:# (unzip.py /def unzip/ /^$/)
```py
def unzip(filename):
    """Generator that yields files in the given zip archive."""
    with zipfile.ZipFile(filename, 'r') as archive:
        for zipinfo in archive.infolist():
            yield archive.open(zipinfo, 'r'), {
                'name': zipinfo.filename,
            }
```

We'll also define a `main` function to verify the function works as expected:

[embedmd]:# (unzip.py /def main/ /^$/)
```py
def main(filenames):
    for filename in filenames:
        for srcfile, metadata in unzip(filename):
            with open(metadata['name'], 'w') as f:
                f.write(srcfile.read())
```

You can find the complete file [here][unzip.py]. Running it produces:

    $ python unzip.py aesop_fables_volume_one_librivox_64kb_mp3.zip
    $ ls
    fables_01_00_aesop_64kb.mp3
    fables_01_01_aesop_64kb.mp3
    fables_01_02_aesop_64kb.mp3
    fables_01_03_aesop_64kb.mp3
    fables_01_04_aesop_64kb.mp3
    ...

which confirms that our unzipping process works as expected.

Now that we have the `mp3` contents of the zip archive, we must transcode that
to a format the API accepts. Currently, for audio longer than 1 minute, the
audio must be in raw, monoaural, 16-bit little-endian format. We'll also make an
attempt to preserve the original sample rate.

[embedmd]:# (convert_audio.py /def mp3_to_raw/ /^ *}/)
```py
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
```

Again, we can define a `main` function to verify the function works as expected:

[embedmd]:# (convert_audio.py /def main/ /print.metadata.*/)
```py
def main(mp3_filenames):
    for mp3_filename in mp3_filenames:
        print('Converting {}'.format(mp3_filename))
        with open(mp3_filename, 'r') as f:
            raw_data, metadata = mp3_to_raw(
                f.read(), {'name': mp3_filename})
        with open(metadata['name'], 'w') as f:
            f.write(raw_data)

        print(metadata)
```

You can find the complete file [here][convert_audio.py]. Running it produces:

    $ python convert_audio.py fables_01_02_aesop_64kb.mp3
    Converting fables_01_02_aesop_64kb.mp3
    {'rate': 24000, 'name': 'fables_01_02_aesop_64kb.raw', 'size': 3214080}

We've now processed our source data into a format ready to be consumed by the
Speech API.

## Transcribe the audio using the Speech API

To extract text data from our prepared audio file, we issue an asynchronous
request to the [Google Cloud Speech API][speech], then poll the API until it
finishes transcribing the file.

### Upload the audio file to Cloud Storage

Because the audio we're transcribing is longer than a minute in length, we must
first upload the raw audio files to [Cloud Storage][storage], so the Speech API
can access it asynchronously. We could use the
[gsutil][gsutil] tool to do this manually, or we could
do it programmatically from our code. Because we'd like to eventually
[automate this process in a pipeline](/community/tutorials/data-science-preprocessing/),
we'll do this in code:

[gsutil]: /storage/docs/quickstart-gsutil
[embedmd]:# (stage_raw.py /def stage_audio/ /return.*/)
```py
def stage_audio(data, metadata, destination_bucket=DESTINATION_BUCKET):
    client = storage.Client()
    blob = client.bucket(destination_bucket).blob(metadata['name'])
    blob.upload_from_string(data, content_type='application/octet-stream')

    return destination_bucket, metadata['name'], metadata
```

You can find the complete file [here][stage_raw.py]. Running it produces:

    $ python stage_raw.py fables_01_02_aesop_64kb.raw --bucket=your-bucket
    Uploading fables_01_02_aesop_64kb.raw
    (u'your-bucket', u'fables_01_02_aesop_64kb.raw', {'name': 'fables_01_02_aesop_64kb.raw'})

### Make the Speech API call

All calls to the Speech API must be authenticated, so make sure you've set up
your service account correctly, as mentioned in the
[prerequisites](#prerequisites). In the following code, we'll use the API's
[client library][speech-client] to create an authenticated service object, which
we'll use to make the API call.

[embedmd]:# (transcribe.py /def transcribe/ /return.*/)
```py
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
```

Since the audio files are longer than a minute, we make the call asynchronously,
and must poll the API for the result:

[embedmd]:# (transcribe.py /def _poll/ /return.*/)
```py
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
```

You can find the complete file [here][transcribe.py]. Running it produces:

    $ python transcribe.py --rate=24000 gs://data-science-getting-started/fables_01_02_aesop_64kb.raw --size=3214080
    (0.982679188251): this is a LibriVox recording all LibriVox recordings are in the public domain for more information or to volunteer please visit librivox.org

    (0.950583994389):  Aesop's Fables the goose that laid the golden egg

    (0.941175699234):  a man and his wife had the Good Fortune to possessive which laid the golden egg everyday lucky though they were they soon begin to think that they were not getting rich fast and and Imagining the bird must be made of gold inside they decided to kill it in order to secure the whole store of precious metal at 1 but when they cut it open a found it was just like any other Goose this thing either got rich all at once as they had hoped you enjoyed any longer the daily addition to their well much once more and Luther

    (0.80675303936):  Inns of the goose that laid the golden egg

## Analyze the syntax

A text transcription of audio is fine and good, but natural language is hard to
glean meaningful insight from, since it's difficult for machines to glean its
structure. For this, we can leverage the
[Cloud Natural Language API][natural-language] to extract the syntax from the
text.

With the Natural Language API, parsing the syntax of the text is a simple API
call:

[embedmd]:# (sentence_structure.py /def extract_syntax/ /return.*/)
```py
def extract_syntax(transcriptions, metadata):
    """Extracts tokens in transcriptions using the Natural Language API."""
    client = language.Client()

    document = client.document_from_text(
            '\n'.join(transcriptions), language='en',
            encoding=_get_native_encoding_type())
    # Only extracting tokens here, but the API also provides these other things
    sentences, tokens, sentiment, entities, lang = document.annotate_text(
            include_syntax=True, include_entities=False,
            include_sentiment=False)

    return tokens, metadata
```

We can write a short `main` function to confirm it works:

[embedmd]:# (sentence_structure.py /def main/ /print.*/)
```py
def main(input_files):
    for line in fileinput.input(input_files):
        logging.info('Analyzing "{}"'.format(line))

        tokens, metadata = extract_syntax([line], {})
        for token in tokens:
            print('{}: {}'.format(token.text_content, token.part_of_speech))
```

You can find the complete file [here][sentence_structure.py]. Running it on a
sample phrase produces:

    $ python sentence_structure.py - <<EOF
    Everyone shall sit under their own vine and fig tree, and no one shall make them afraid.
    EOF

    Everyone: NOUN
    shall: VERB
    sit: VERB
    under: ADP
    their: PRON
    own: ADJ
    vine: NOUN
    and: CONJ
    fig: NOUN
    tree: NOUN
    ,: PUNCT
    and: CONJ
    no: DET
    one: NOUN
    shall: VERB
    make: VERB
    them: PRON
    afraid: ADJ
    .: PUNCT

We've now gone from a stream of spoken prose, transformed it into a form
readable by our tools, and came out with a structured catalog of its contents.
In this form, we can unleash our exploratory tools, as described in the
[Exploratory Queries](/community/tutorials/data-science-exploration/) article.

[comment]: # (and [Visualization with interactive notebooks].)

But first, it's imperative that we go from manually transforming this data with
a series of scripts, to
[automating this process](/community/tutorials/data-science-preprocessing/).

## API Documentation and other resources

We've only touched on a couple of the capabilities of the APIs we've used here.
Take a look at the API documentation, and experiment with the other features.

* Speech API ([API Docs][speech-docs] | [Client Library Docs][speech-client])
* Natural Language API ([API Docs][natural-language-docs] | [Client Library Docs][language-client])
* Vision API ([API Docs][vision-docs] | [Client Library Docs][vision-client])
* Translate API ([API Docs][translate-docs] | [Client Library Docs][translate-client])

Also, take a look at the [Structuring Unstructured text][unstructured-text] demo
for another example of using the Natural Language API.

[speech-docs]: /speech/docs
[natural-language-docs]: /natural-language/docs
[vision-docs]: /vision/docs
[translate-docs]: /translate/docs
[speech-client]: //googlecloudplatform.github.io/google-cloud-python/stable/speech-usage.html
[language-client]: //googlecloudplatform.github.io/google-cloud-python/stable/language-usage.html
[vision-client]: //googlecloudplatform.github.io/google-cloud-python/stable/vision-usage.html
[translate-client]: //googlecloudplatform.github.io/google-cloud-python/stable/translate-usage.html
[unstructured-text]: /blog/big-data/2016/08/structuring-unstructured-text-with-the-google-cloud-natural-language-api

## What's next

The astute among you may notice that the return values of each of these steps
feeds right into the arguments to the next. Indeed - it would make sense to tie
all these functions together into a pipeline that can be automated, depositing
the results into a database for later querying.

In fact, the [next step](/community/tutorials/data-science-preprocessing/)
describes how to tie functions like these together into a preprocessing
pipeline, using the [Dataflow][dataflow] service.

[dataflow]: /dataflow

[convert_audio.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-extraction/convert_audio.py
[sentence_structure.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-extraction/sentence_structure.py
[stage_raw.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-extraction/stage_raw.py
[transcribe.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-extraction/transcribe.py
[unzip.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-extraction/unzip.py
