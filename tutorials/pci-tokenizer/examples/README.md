# GCP Cloud Run tokenization example scripts

Simple utilities to demonstrate tokenization and detokenization of credit card numbers. Not for production use.

## Installation

These scripts are only usable after installing your Cloud Run tokenization service. See [../index.md](../index.md) for more
information.

## Configuration

Before you can run the tokenizer, you must provide the URL of the project running the Cloud Run tokenization service in the
file `envvars`. You will need to provide the name of the project if you didn't enter it into the service config file.

## Usage

### Tokenizing

The simplest example is to call the tokenizer with no parameters. Default values, including a dummy credit card number will 
be used:

```
./tokenize

Adjql3+3eoufWD/b0My7AWG2R7LF4KZPmX/VeBIgDUzxlEkrrA0Wn+GXCOqvdVhXEe0x
```

You can provide your own values, too. The parameters are CC, expiration MM, expiration YYYY, and userID. The userID can be 
any string value and is used to assist in validating the detokenization.

```
./tokenize 5454545454545454 12 2029 1234567

BV3VH5ErFA+5ZNgDgRK6aWsYEWum6wcvPLPOXC/0fX3FMROA/G6A7dhaq0b7sy+j6N4=
```

### Detokenizing

To reverse the tokenization example, pass the token as the first argument and optionally the userID as the second argument:

```
./detokenize BV3VH5ErFA+5ZNgDgRK6aWsYEWum6wcvPLPOXC/0fX3FMROA/G6A7dhaq0b7sy+j6N4=

{"cc":"5454545454545454","mm":"12","yyyy":"2029"}
```

### Batch tokenizing

Install required Python modules:

```commandline
pip3 install -r requirements.txt
```

The simplest example is to call `batch_tokenize.sh` with the sample CSV file in the `csv_files` directory. 
The CSV file includes some example credit card data.

```
./batch_tokenize.sh csv_files/batch_tokenize_sample_csv.csv 
```

You can find the output CSV file `batch_tokenize_sample_csv_output.csv` in the `csv_files` directory.

### Batch detokenizing

For detokenizing, update the `batch_detokenize_sample_csv.csv` file in the `csv_files` directory with tokenized data.

Run the following command for batch detokenizing:

```
./batch_detokenize.sh csv_files/batch_detokenize_sample_csv.csv 
```

You can find the output CSV file `batch_detokenize_sample_csv_output.csv` in the `csv_files` directory.

If you get a validation error, ensure that the userID matches.

## License

[Apache-2.0](http://www.apache.org/licenses/LICENSE-2.0)
