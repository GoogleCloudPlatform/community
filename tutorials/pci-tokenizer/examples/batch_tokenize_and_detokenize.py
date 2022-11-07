#!/bin/env python3

"""
This is an example script to tokenize or detokenize batch data using CSV file.

Usage: batch_tokenize_and_detokenize.py [options]

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
  --transformation_type=TRANSFORMATION_TYPE
                        Specify if you want to tokenize or detokenize

Output:
In case of tokenizer, output file is csv_files/batch_tokenize_sample_csv_output.csv
In case of detokenizer, output file is csv_files/batch_detokenize_sample_csv_output.csv

"""
import json
import optparse
import requests
import sys
import csv


def parse_csv_and_send_tokenize_request(csv_file_path, auth_token, project_id, app_url):
    """
    This function is used to parse CSV file and create a json which will be used send to tokenizer service
    as POST API call data
    """
    with open(csv_file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            data_dic = {"cc": row[0], "mm": row[1], "yyyy": row[2], "user_id": row[3], "project_id": project_id}
            send_tokenize_request(auth_token, data_dic, app_url)


def send_tokenize_request(auth_token, data_dic, app_url):
    """
    This function is used to send POST API call to tokenizer service URL with the data from CSV file
    """
    auth_token = "Bearer " + auth_token
    headers = {"authorization": auth_token, "content-type": "application/json"}

    response = requests.request("POST", app_url, json=data_dic, headers=headers)
    if response.status_code == 200:
        resp_data = response.text
    else:
        resp_data = "Error while tokenizing"
        print(resp_data, response.status_code, print(response.text))
    write_tokenized_output_in_csv(data_dic, resp_data)


def write_tokenized_output_in_csv(data_dic, resp_data):
    """
    This function is used to write final CSV file with tokenized data
    """
    row = [data_dic["cc"], data_dic["mm"], data_dic["yyyy"], data_dic["user_id"], resp_data]
    data_file = open("csv_files/batch_tokenize_sample_csv_output.csv", "a")
    writer = csv.writer(data_file)
    writer.writerow(row)
    data_file.close()


def parse_csv_and_send_detokenize_request(csv_file_path, auth_token, project_id, app_url):
    """
    This function is used to parse CSV file and create a json which will be used send to detokenizer service
    as POST API call data
    """
    with open(csv_file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            data_dic = {"user_id": row[0], "token": row[1], "project_id": project_id}
            send_detokenize_request(auth_token, data_dic, app_url)


def send_detokenize_request(auth_token, data_dic, app_url):
    """
    This function is used to send POST API call to detokenizer service URL with the data from CSV file
    """
    auth_token = "Bearer " + auth_token
    headers = {"authorization": auth_token, "content-type": "application/json"}

    response = requests.request("POST", app_url, json=data_dic, headers=headers)
    if response.status_code == 200:
        resp_data = json.loads(response.content)
        write_detokenized_output_in_csv(data_dic, resp_data)
    else:
        resp_data = "Error while detokenizing"
        print(resp_data, response.status_code, response.text)


def write_detokenized_output_in_csv(data_dic, resp_data):
    """
    This function is used to write final CSV file with detokenized data
    """
    row = [resp_data["cc"], resp_data["mm"], resp_data["yyyy"], data_dic["user_id"], data_dic["token"]]
    data_file = open("csv_files/batch_detokenize_sample_csv_output.csv", "a")
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
    parser.add_option('--transformation_type', help="Specify if you want to tokenize or detokenize")
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

    if options.transformation_type:
        transformation_type = options.transformation_type
    else:
        raise Exception('Invalid or missing --transformation_type option')

    if transformation_type == "tokenize":
        header = ["CC", "MM", "YYYY", "USER_ID", "TOKENIZED_DATA"]
        data_file = open("csv_files/batch_tokenize_sample_csv_output.csv", "w")
        writer = csv.writer(data_file)
        writer.writerow(header)
        data_file.close()
        parse_csv_and_send_tokenize_request(csv_file_path, auth_token, project_id, app_url)
    elif transformation_type == "detokenize":
        header = ["CC", "MM", "YYYY", "USER_ID", "TOKENIZED_DATA"]
        data_file = open("csv_files/batch_detokenize_sample_csv_output.csv", "w")
        writer = csv.writer(data_file)
        writer.writerow(header)
        data_file.close()
        parse_csv_and_send_detokenize_request(csv_file_path, auth_token, project_id, app_url)
    else:
        print("Wrong transformation_type provided, transformation_type should be either tokenizer or detokenizer")


if __name__ == '__main__':
    main(sys.argv[1:])
