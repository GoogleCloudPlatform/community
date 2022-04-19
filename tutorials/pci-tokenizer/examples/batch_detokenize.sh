#!/usr/bin/env bash
# This script demonstrates the invocation of the batch_tokenize_and_detokenize.py script. It should
# be run from a machine with an identity or service account authorized to call
# your Cloud Run tokenization service.
# This script uses batch_tokenize_sample_csv.csv file as input and
# final outdup get dumped into batch_tokenize_sample_csv_output.csv
# See the readme for more information.

# Usage:
# ./batch_detokenize.sh <CSV_FILE_PATH>
# Example values will be provided for any missing input

# Output:
# output file is csv_files/batch_detokenize_sample_csv_output.csv

. $(dirname "$0")/envvars
test -f $(dirname "$0")/local.envvars && . $(dirname "$0")/local.envvars

if [ "$1" = "" ]; then
  CSV_FILE_PATH="csv_files/batch_detokenize_sample_csv.csv"
else
  CSV_FILE_PATH=$1
fi

AUTH=$(gcloud auth print-identity-token)
echo $(python3 batch_tokenize_and_detokenize.py --csv_file_path "$CSV_FILE_PATH" --auth_token "$AUTH" --project_id "$PROJECT" --app_url "$URL/detokenize" --transformation_type "detokenize")
