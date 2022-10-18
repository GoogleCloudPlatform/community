# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

YOUR_PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']

# [START bigquery_ibis_connect]
import ibis
import ibis_bigquery

conn = ibis_bigquery.connect(
    project_id=YOUR_PROJECT_ID,
    dataset_id='bigquery-public-data.stackoverflow')
# [END bigquery_ibis_connect]

# [START bigquery_ibis_table]
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
# [END bigquery_ibis_table]

# [START bigquery_ibis_table_not_exist]
try:
    doesnt_exist = conn.table('doesnt_exist')
except Exception as exp:
    print(str(exp))
    # Not found: Table bigquery-public-data:stackoverflow.doesnt_exist
# [END bigquery_ibis_table_not_exist]

# [START bigquery_ibis_table_cross_project]
reddit_posts_table = conn.table('2018_05', database='fh-bigquery.reddit_posts')
# [END bigquery_ibis_table_cross_project]

# [START bigquery_ibis_type_error]
try:
    table.answer_count.upper()
except AttributeError as exp:
    print(str(exp))
    # 'IntegerColumn' object has no attribute 'upper'
# [END bigquery_ibis_type_error]

# [START bigquery_ibis_projection]
projection = table['creation_date', 'answer_count']
# [END bigquery_ibis_projection]

# [START bigquery_ibis_transform_timestamp]
projection = projection.mutate(year=projection.creation_date.year())
# [END bigquery_ibis_transform_timestamp]

# [START bigquery_ibis_transform_integer]
has_answer_boolean = projection.answer_count > 0
# [END bigquery_ibis_transform_integer]
# [START bigquery_ibis_transform_boolean]
has_answer_int = has_answer_boolean.ifelse(1, 0)
# [END bigquery_ibis_transform_boolean]

# [START bigquery_ibis_aggregate]
total_questions = projection.count()
percentage_answered = has_answer_int.mean() * 100
# [END bigquery_ibis_aggregate]

# [START bigquery_ibis_group_by]
expression = projection.groupby('year').aggregate(
    total_questions=total_questions,
    percentage_answered=percentage_answered,
).sort_by(ibis.desc(projection.year))
# [END bigquery_ibis_group_by]

print('\nExecuting query:')
# [START bigquery_ibis_execute]
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
# [END bigquery_ibis_execute]

print('\nThe previous query used the following SQL:')
# [START bigquery_ibis_compile]
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
# [END bigquery_ibis_compile]

# print('\nExecuting UDF query:')
# [START bigquery_ibis_udf]
import ibis.expr.datatypes as dt

@ibis_bigquery.udf(['double'], dt.double())
def example_udf(value):
    return value + 1.0

test_column = ibis.literal(1, type=dt.double())
expression = example_udf(test_column)

print(conn.execute(expression))
# [END bigquery_ibis_udf]

print('\nExecuting join query:')
# [START bigquery_ibis_joins]
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
# [END bigquery_ibis_joins]
