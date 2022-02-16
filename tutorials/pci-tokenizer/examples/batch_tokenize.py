#!/bin/env python3

"""
This is an example script to tokenize or detokenize batch data using CSV file.

Usage: batch_tokenize.py [options]

Tokenize or Detokenize using CSV file. Please make sure you have updated
envvars file

Options:
  -h, --help            show this help message and exit
  --csv_file_path=CSV_FILE_PATH
                        Specify the path of CSV file, example
                        /home/user/abc.csv
  --auth_token=AUTH_TOKEN
                        Specify the auth token for Google Cloud authentication
  --project_id=PROJECT_ID
                        Specify GCP project id
  --app_url=APP_URL     Specify App URL

"""
import json
import optparse
import requests
import sys
import csv


def parse_csv_and_send_tokenize_request(csv_file_path, auth_token, project_id, app_url):
    """
    This function is used to parse CSV file and create a json which will be used send to tokenizer service
    as API data
    """
    data_dic = {}
    with open(csv_file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            data_dic = {"cc": row[0], "mm": row[1], "yyyy": row[2], "user_id": row[3], "project_id": project_id}
            send_tokenize_request(auth_token, data_dic, app_url)


def send_tokenize_request(auth_token, data_dic, app_url):
    """
    This function is used to send API call to tokenizer service URL with the data from CSV file
    """
    auth_token = "Bearer " + auth_token
    headers = {"authorization": auth_token, "content-type": "application/json"}

    response = requests.request("POST", app_url, json=data_dic, headers=headers)
    if response.status_code == 200:
        resp_data = response.text
    else:
        resp_data = "Error while tokenizing"
        print(response.status_code, print(response.text))
    write_output_in_csv(data_dic, resp_data)


def write_output_in_csv(data_dic, resp_data):
    """
    This function is used to write final CSV file with tokenized data
    """
    row = [data_dic["cc"], data_dic["mm"], data_dic["yyyy"], data_dic["user_id"], resp_data]
    data_file = open("batch_tokenize_sample_csv_output.csv", "a")
    writer = csv.writer(data_file)
    writer.writerow(row)
    data_file.close()


def main(args):
    parser = optparse.OptionParser(description="Tokenize or Detokenize using CSV file. Please make sure you have "
                                               "updated envvars file")
    parser.add_option('--csv_file_path', help="Specify the path of CSV file, example /home/user/abc.csv")
    parser.add_option('--auth_token', help="Specify the auth token for Google Cloud authentication")
    parser.add_option('--project_id', help="Specify GCP project id")
    parser.add_option('--app_url', help="Specify App URL")
    options, remaining_args = parser.parse_args(args)

    if options.csv_file_path:
        csv_file_path = options.csv_file_path
    else:
        raise Exception('Invalid or missing --csv_file_path option')

    if options.auth_token:
        auth_token = options.auth_token
    else:
        raise Exception('Invalid or missing --auth_token option')

    if options.project_id:
        project_id = options.project_id
    else:
        raise Exception('Invalid or missing --project_id option')

    if options.app_url:
        app_url = options.app_url
    else:
        raise Exception('Invalid or missing --app_url option')

    header = ["CC", "MM", "YYYY", "USER_ID", "TOKENIZED_DATA"]
    data_file = open("batch_tokenize_sample_csv_output.csv", "w")
    writer = csv.writer(data_file)
    writer.writerow(header)
    data_file.close()

    parse_csv_and_send_tokenize_request(csv_file_path, auth_token, project_id, app_url)


if __name__ == '__main__':
    main(sys.argv[1:])
