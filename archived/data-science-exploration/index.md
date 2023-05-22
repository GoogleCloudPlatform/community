---
title: Exploratory queries with BigQuery
description: Use BigQuery to investigate arbitrarily large datasets.
author: jerjou
tags: Data Science, BigQuery
date_published: 2017-05-23
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Google Cloud includes a variety of data services. When you're
encountering new data you'd like to explore, [BigQuery](/bigquery) allows
you to do so easily and scalably. It is a fully-managed service for data
exploration on arbitrarily-large datasets using an SQL syntax. Once data
has been loaded into the service, it can be queried at interactive speeds,
without having to know beforehand what you're looking for.

There has been much already written about using BigQuery for data analysis - for
example:

* [Analyzing Financial Time Series using BigQuery](/solutions/time-series/bigquery-financial-forex)
* [How to forecast demand with Google BigQuery, public datasets and TensorFlow](/blog/big-data/2016/05/how-to-forecast-demand-with-google-bigquery-public-datasets-and-tensorflow)
* The interesting sample queries for the
  [BigQuery Public Datasets](/bigquery/public-data/)

In this tutorial, we'll explore the data that we've
[preprocessed](/community/tutorials/data-science-preprocessing/) and
[extracted](/community/tutorials/data-science-extraction/) as part of other
tutorials in this series.

## Meteorite Landing data

In the [preprocessing](/community/tutorials/data-science-preprocessing/)
tutorial, we cleaned and ingested records of every meteorite landing known to
The Meteoritical Society.  Now that it's in BigQuery, let's see what we can
learn from it.

For this tutorial, we'll reference the public BigQuery table
`[data-science-getting-started:preprocessing.meteors]`, but you can replace that
with the table you created as well.

Let's start exploring this data. You can use either the `bq` command included in
the [Cloud SDK](/sdk), or head over to the [web interface][bq-web].
Let's get an idea of our data first:

    $ bq query "select * \
      from [data-science-getting-started:preprocessing.meteors] \
      limit 10"

    Waiting on bqjob_r725b1cfcd18745e_00000158e640fc9c_1 ... (0s) Current status: DONE
    +-------+------+----------+---------+-----------------------------+-------+-----------+------------+-------+
    | fall  | year | nametype |  mass   |            name             | class | latitude  | longitude  |  id   |
    +-------+------+----------+---------+-----------------------------+-------+-----------+------------+-------+
    | Found | 2001 | Valid    |   140.0 | Dhofar 402                  | H6    |  19.30017 |   54.53572 | 7184  |
    | Found | 2003 | Valid    |   94.29 | Grove Mountains 022163      | L5    | -72.78167 |   75.30389 | 46588 |
    | Found | 1993 | Valid    |    26.2 | Queen Alexandra Range 93279 | L5    |     -84.0 |      168.0 | 19367 |
    | Found | 1994 | Valid    |     0.9 | Queen Alexandra Range 94512 | H5    |     -84.0 |      168.0 | 20144 |
    | Found | 2005 | Valid    |   112.9 | Randsburg                   | L5    |   35.4005 | -117.66617 | 44798 |
    | Found | 1986 | Valid    |    3.18 | Yamato 86222                | H4    |     -71.5 |   35.66667 | 29728 |
    | Found | 1981 | Valid    |    26.8 | Clarendon (b)               | H5    |  34.93611 | -100.94167 | 5370  |
    | Found | 1931 | Valid    | 31500.0 | Ioka                        | L3.5  |     40.25 | -110.08333 | 12040 |
    | Found | 1986 | Valid    |    4.13 | Yamato 86734                | L5    |     -71.5 |   35.66667 | 30240 |
    | Found | 2003 | Valid    |   19.67 | Grove Mountains 021569      | H4    | -72.94028 |   75.28583 | 46552 |
    +-------+------+----------+---------+-----------------------------+-------+-----------+------------+-------+
    $

[bq-web]: https://bigquery.cloud.google.com/table/data-science-getting-started:preprocessing.meteors?pli=1&tab=preview

Okay, so there are several bits of information that the Meteoritical Society
provides us. From this sample, the `fall` field is always set to `Found`. Let's
see if there are any other values using a `group by`:

    $ bq query "select fall, count(*) \
      from [data-science-getting-started:preprocessing.meteors] \
      group by fall"

    Waiting on bqjob_r53d4aa00496894f3_00000158e6472c6e_1 ... (0s) Current status: DONE
    +-------+-------+
    | fall  |  f0_  |
    +-------+-------+
    | Found | 30941 |
    | Fell  |  1096 |
    +-------+-------+

It seems it's far more likely (96.6% vs 3.4%) for a meteor to be found, than to
be seen fall. This is reassuring, since by extension it implies that it's
unlikely that a meteor will fall on any given person. But how frequently do they
fall in general? The data only provides information for the actual fall of `1096
/ (1096 + 30941) = 3.4%` of the recorded meteors, but a count of meteors by year
should at least give us a rough upper bounds for the frequency of meteors
falling:

    $ bq query "select year,count(*) \
      from [data-science-getting-started:preprocessing.meteors] \
      group by year \
      order by year desc \
      limit 10"

    Waiting on bqjob_reddf21b4589a88f_00000158e6916f3e_1 ... (0s) Current status: DONE
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

It looks like 2006 was a good year for meteors.

**Aside**: Doing queries like this can serve to inform the
[preprocessing](/community/tutorials/data-science-preprocessing/) step,
revealing bugs and dirty data. For example, the first draft of this article
revealed some bad `year` data, which led directly to filters incorporated into
the [cleansing pipeline][clean.py].

    $ bq query "select year, count(*) \
      from [data-science-getting-started:preprocessing.meteors] \
      group by year \
      order by year asc \
      limit 10"

    Waiting on bqjob_r48f3c95595baa8e7_00000158e66599ba_1 ... (0s) Current status: DONE
    +------+-----+
    | year | f0_ |
    +------+-----+
    | -250 |   1 |
    |  -60 |   1 |
    |  -30 |   1 |
    |  861 |   1 |
    |  921 |   1 |
    | 1400 |   1 |
    | 1491 |   1 |
    | 1492 |   1 |
    | 1496 |   1 |
    | 1520 |   1 |
    +------+-----+

[embedmd]:# (/community/tutorials/data-science-preprocessing/clean.py /def filter_suspicious/ /yield.*$/)
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

[clean.py]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/data-science-preprocessing/clean.py

You might then ask whether the 2006 figure is normal. BigQuery provides a
function to approximate
[quantiles](/bigquery/docs/reference/legacy-sql#quantiles), which
gives us an idea of the distribution:

    $ bq query "select quantiles(c, 11) \
      from (select year,count(*) as c \
      from [data-science-getting-started:preprocessing.meteors] \
      group by year)"

    Waiting on bqjob_r5e37ad4ae7eb9f1d_00000158e6a989f2_1 ... (0s) Current status: DONE
    +------+
    | f0_  |
    +------+
    |    1 |
    |    1 |
    |    1 |
    |    3 |
    |    7 |
    |   10 |
    |   14 |
    |   19 |
    |   31 |
    |  344 |
    | 3046 |
    +------+

This tells us that the median number of meteors found per year is 10, the
most meteors found in a year is 3046, with 90% of years recording less than 344
meteors. The `quantile` function provides approximate figures, but can give us a
decent impression of the overall shape of the data. We can compute a more
precise figure manually:

    $ bq query "select count(*) \
      from (select year, count(*) as total \
      from [data-science-getting-started:preprocessing.meteors] \
      group by year) \
      where total > 344"

    Waiting on bqjob_r773b54da6065da90_00000159092886d0_1 ... (0s) Current
    status: DONE
    +-----+
    | f0_ |
    +-----+
    |  27 |
    +-----+

    $ bq query "select count(distinct year) \
      from [data-science-getting-started:preprocessing.meteors]"

    Waiting on bqjob_r10875cdc43c2016c_00000159092e5b4b_1 ... (0s) Current status: DONE
    +-----+
    | f0_ |
    +-----+
    | 262 |
    +-----+

So we find for the 262 years for which we have data, `27 / 262 = 10%` of the
years recorded more than 344 meteors. So in that sense, 2006 was indeed an
unusual year, though the same could be said of 2010 and 2011. In fact, recent
years do seem to have a higher number of reported meteors relative to the
quantile distribution, perhaps due to more vigilant record-keeping. We can again
use the `quantiles` function to get an overall impression of how reporting is
distributed across the years:

    $ bq query "select quantiles(year, 11) \
      from [data-science-getting-started:preprocessing.meteors]"

    Waiting on bqjob_r1173c8efd6d56896_00000159093f2769_1 ... (0s) Current status:
    DONE
    +------+
    | f0_  |
    +------+
    | 1400 |
    | 1974 |
    | 1979 |
    | 1985 |
    | 1988 |
    | 1991 |
    | 1995 |
    | 1999 |
    | 2001 |
    | 2003 |
    | 2013 |
    +------+

We see here that the period from 1400 to 1974 has roughly the same number of
reported meteors as the period from 2003 to 2013, though from 1974 onward, there
seems to have fairly regular reporting.

Quantiles are useful for getting a quick feel for the distribution of your data
- try using it to find the different masses of meteors found.

Finally, one might be concerned, when researching a new place to live or
establish a business, the rate you might expect meteors to land in your area.
Fortunately, BigQuery provides some functions to help compute distances between
latitude and longitude coordinates. Adapted from the
[advanced examples](/bigquery/docs/reference/legacy-sql#math-adv-examples) in
the docs, we can find the number of meteors within an approximately 50-mile
radius of Google's Kirkland campus (at 47.669861, -122.197355):

    $ bq query "select fall, year, mass, name, class, distance_miles \
      from (select *, \
       ((ACOS(SIN(47.669861 * PI() / 180) * \
              SIN(latitude  * PI() / 180) + \
              COS(47.669861 * PI() / 180) * \
              COS(latitude  * PI() / 180) * \
              COS((-122.197355 - longitude) * PI() / 180)) * \
         180 / PI()) * \
        60 * 1.1508) as distance_miles \
       from [data-science-getting-started:preprocessing.meteors]) \
      where distance_miles < 50"

    Waiting on bqjob_rcabb65ad2a85268_000001590993e5f7_1 ... (0s) Current status: DONE
    +-------+------+------+--------+-------------------+--------------------+
    | fall  | year | mass |  name  |       class       |   distance_miles   |
    +-------+------+------+--------+-------------------+--------------------+
    | Found | 1925 | 16.7 | Tacoma | Iron, IAB complex | 30.745345223426092 |
    +-------+------+------+--------+-------------------+--------------------+

Since the last meteor was found before I was born, 30 miles away, it seems that
Kirkland is relatively safe from meteor landings.

The natural next step in making this information useful and presentable might be
to create a visualization of this on a map, since this is inherently geographic
data. For more on this, check out [Datalab](/datalab) and
[Datastudio](//www.google.com/analytics/data-studio/).

## API Documentation

BigQuery is not just a command-line sql querying tool -

* As we've seen, in addition to support for
  [standard SQL](/bigquery/docs/reference/standard-sql/) (and its
  [legacy SQL](/bigquery/docs/reference/legacy-sql) syntax used in this
  tutorial), BigQuery also provides some useful additional aggregate functions.
* There's also has an extensive
  [REST API with client libraries](/bigquery/docs/reference/) for programmatic
  management and querying of data within BigQuery.
* Other Google Cloud tools integrate with BigQuery, such as
    * using BigQuery as a data source and/or sink in a
      [Dataflow](/dataflow) pipeline, as demonstrated in the
      [preprocessing](/community/tutorials/data-science-preprocessing/) tutorial.
    * performing BigQuery queries directly from a
      [Datalab notebook](//cloud.google.com/bigquery/docs/visualize-datalab)
    * creating graphs in [Data Studio](/bigquery/docs/visualize-data-studio).
