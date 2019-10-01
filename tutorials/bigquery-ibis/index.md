---
title: Query BigQuery With Python Using Ibis
description: Learn how to use the Ibis Python library to query BigQuery tables without writing SQL code.
author: tswast
tags: BigQuery, Ibis, Python, Data Science
date_published: 2018-08-13
---

[Ibis](http://ibis-project.org/) is a Python library for doing data
analysis. It offers a Pandas-like environment for executing data analysis in
big data processing systems such as BigQuery. Ibis's primary goals are to be
a type safe, expressive, composable, and familiar replacement for SQL.

In this tutorial, you'll use Ibis to query the [Stack Overflow public dataset
in BigQuery](https://cloud.google.com/bigquery/public-data/stackoverflow).

## Objectives

- Query BigQuery using Ibis.
- Join multiple BigQuery tables together.
- Write a BigQuery user-defined function (UDF) in Python.

## Before you begin

Follow the instructions in the following guides to set up your environment to
develop Python code that connects to Google Cloud Platform:

1.  [Set up a Python development environment](https://cloud.google.com/python/setup).
1.  [Authenticate to Google Cloud Platform with a service
    account](https://cloud.google.com/docs/authentication/getting-started).

## Costs

This tutorial uses billable components of Cloud Platform including
BigQuery. Use the [Pricing
Calculator](https://cloud.google.com/products/calculator/#id=d343aa2d-457b-4778-b4cb-ef0ea35605ea)
to estimate the costs for your usage.

The first 1 TB per month of BigQuery queries are free. See [the BigQuery
pricing documentation](https://cloud.google.com/bigquery/pricing) for more
details about on-demand and flat-rate pricing. BigQuery also offers [controls
to limit your costs](https://cloud.google.com/bigquery/cost-controls).

## Install Ibis with BigQuery integrations

Install Ibis from the latest version on GitHub, because this tutorial
requires some features which are not yet released, such as the ability to
query public datasets.

```
pip install --upgrade git+https://github.com/ibis-project/ibis.git#egg=ibis_framework[bigquery]
```

## Connect to BigQuery

Use the `connect()` function to authenticate with BigQuery and set the
default dataset for queries.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_connect.*/ /END bigquery_ibis_connect]/)
```py
import ibis

conn = ibis.bigquery.connect(
    project_id=YOUR_PROJECT_ID,
    dataset_id='bigquery-public-data.stackoverflow')
```

## Build an expression

Build an [Ibis
expression](http://docs.ibis-project.org/design.html#expressions)
representing the query you'd like to run. Follow the instructions in this
example to build a query expression that determines the percentage of Stack
Overflow questions with answers, grouped by year.

### Get a table

The first step in building most Ibis expressions is to choose a table to
query. Select the `bigquery-public-data.stackoverflow.post_questions` table.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_table.*/ /END bigquery_ibis_table]/)
```py
table = conn.table('posts_questions')
print(table)
# BigQueryTable[table]
# name: bigquery-public-data.stackoverflow.posts_questions
# schema:
#   id : int64
#   title : string
#   body : string
#   accepted_answer_id : int64
#   answer_count : int64
#   comment_count : int64
#   community_owned_date : timestamp
#   creation_date : timestamp
#   favorite_count : int64
#   last_activity_date : timestamp
#   last_edit_date : timestamp
#   last_editor_display_name : string
#   last_editor_user_id : int64
#   owner_display_name : string
#   owner_user_id : int64
#   post_type_id : int64
#   score : int64
#   tags : string
#   view_count : int64
```

Ibis fetches the table from BigQuery so that is can do validations as you
construct the expression. It throws an error if the table doesn't exist.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_table_not_exist.*/ /END bigquery_ibis_table_not_exist]/)
```py
try:
    doesnt_exist = conn.table('doesnt_exist')
except Exception as exp:
    print(str(exp))
    # Not found: Table bigquery-public-data:stackoverflow.doesnt_exist
```

Pass in the `database` parameter to use tables in other projects.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_table_cross_project.*/ /END bigquery_ibis_table_cross_project]/)
```py
reddit_posts_table = conn.table('2018_05', database='fh-bigquery.reddit_posts')
```

### Select columns

It is important to select only the columns you need for efficient BigQuery
queries. Select just the `creation_date` and `answer_count` columns from the
`post_questions` table, because only these are needed to count the percentage
of answered questions per year.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_projection.*/ /END bigquery_ibis_projection]/)
```py
projection = table['creation_date', 'answer_count']
```

### Transform columns

Call a function on the column to build an expression graph that transforms
the original column. For example, to extract the year from the created date,
call the [`year()` timestamp
method](http://docs.ibis-project.org/api.html#timestamp-methods).

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_transform_timestamp.*/ /END bigquery_ibis_transform_timestamp]/)
```py
projection = projection.mutate(year=projection.creation_date.year())
```

Use a comparison operator on the the `answer_count` method to transform it
into a Boolean that indicates if the question has any answers.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_transform_integer.*/ /END bigquery_ibis_transform_integer]/)
```py
has_answer_boolean = projection.answer_count > 0
```

Use the [`ifelse()` boolean
method](http://docs.ibis-project.org/api.html#boolean-methods) to convert
from a Boolean back to an integer, because you'll be adding this transformed
column to construct the percentage.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_transform_boolean.*/ /END bigquery_ibis_transform_boolean]/)
```py
has_answer_int = has_answer_boolean.ifelse(1, 0)
```

If you make a mistake with the types, you'll find out quickly. Because the
expression contains schema information, Ibis throws an error if you use a
function that doesn't apply to the column's type. For example, it raises an
exception if you try to use a string method on an integer column.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_type_error.*/ /END bigquery_ibis_type_error]/)
```py
try:
    table.answer_count.upper()
except AttributeError as exp:
    print(str(exp))
    # 'IntegerColumn' object has no attribute 'upper'
```

### Aggregate columns

Use the [column
methods](http://docs.ibis-project.org/api.html#column-methods) `count()` and
`sum()` to calculate the percentage of questions answered.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_aggregate.*/ /END bigquery_ibis_aggregate]/)
```py
total_questions = projection.count()
percentage_answered = has_answer_int.mean() * 100
```

### Group by year

Use the
[aggregate()](http://docs.ibis-project.org/generated/ibis.expr.api.TableExpr.aggregate.html#ibis.expr.api.TableExpr.aggregate)
method to combine the aggregations together and group by the year column
expression.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_group_by.*/ /END bigquery_ibis_group_by]/)
```py
expression = projection.groupby('year').aggregate(
    total_questions=total_questions,
    percentage_answered=percentage_answered,
).sort_by(ibis.desc(projection.year))
```

## Executing the query expression

Call the `execute()` method on the expression to run the query with BigQuery.
Ibis executes the query and then returns the results as a Pandas DataFrame.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_execute.*/ /END bigquery_ibis_execute]/)
```py
print(expression.execute())
#     year  total_questions  percentage_answered
# 0   2018           997508            66.776307
# 1   2017          2318405            75.898732
# 2   2016          2226478            84.193197
# 3   2015          2219791            86.170365
# 4   2014          2164895            88.356987
# 5   2013          2060753            91.533241
# 6   2012          1645498            94.510659
# 7   2011          1200601            97.149261
# 8   2010           694410            99.060497
# 9   2009           343879            99.655402
# 10  2008            58399            99.871573
```

If you are curious what SQL code Ibis executed for this query, use the
`compile()` method on the expression.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_compile.*/ /END bigquery_ibis_compile]/)
```py
print(expression.compile())
# SELECT `year`, count(*) AS `total_questions`,
#        (IEEE_DIVIDE(sum(CASE WHEN `answer_count` > 0 THEN 1 ELSE 0 END), count(*))) * 100 AS `percentage_answered`
# FROM (
#   SELECT `creation_date`, `answer_count`,
#          EXTRACT(year from `creation_date`) AS `year`
#   FROM `bigquery-public-data.stackoverflow.posts_questions`
# ) t0
# GROUP BY 1
# ORDER BY `year` DESC
```

## Next Steps

You've just run a query on BigQuery with Ibis. No SQL required! Next, you may
wish to explore how to build more complex queries with Ibis.

### Write a UDF

Ibis supports [user defined functions in
BigQuery](http://docs.ibis-project.org/udf.html#bigquery) by compiling Python
code into JavaScript. This means that you can write UDFs for BigQuery in
Python!

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_udf.*/ /END bigquery_ibis_udf]/)
```py
@ibis.bigquery.udf(['double'], 'double')
def example_udf(value):
    return value + 1.0

test_column = ibis.literal(1, type='double')
expression = example_udf(test_column)

print(conn.execute(expression))
```

### Join multiple tables

Combine multiple tables together in your query expression by using joins.

See the [Table methods](http://docs.ibis-project.org/api.html#api-table)
reference for links to the various join methods. Read the [joins section in
the guide for SQL programmers](http://docs.ibis-project.org/sql.html#joins)
for examples.

[embedmd]:# (ibis_bigquery.py /^.*START bigquery_ibis_joins.*/ /END bigquery_ibis_joins]/)
```py
edu_table = conn.table(
    'international_education',
    database='bigquery-public-data.world_bank_intl_education')
edu_table = edu_table['value', 'year', 'country_code', 'indicator_code']

country_table = conn.table(
    'country_code_iso',
    database='bigquery-public-data.utility_us')
country_table = country_table['country_name', 'alpha_3_code']

expression = edu_table.join(
    country_table,
    [edu_table.country_code == country_table.alpha_3_code])

print(conn.execute(
    expression[edu_table.year == 2016]
        # Adult literacy rate.
        [edu_table.indicator_code == 'SE.ADT.LITR.ZS']
        .sort_by([ibis.desc(edu_table.value)])
        .limit(20)
))
```

### Resources

- [Ibis tutorial](http://docs.ibis-project.org/tutorial.html)
- [Ibis API reference](http://docs.ibis-project.org/api.html)
- [Ibis guide for SQL programmers](http://docs.ibis-project.org/sql.html)
