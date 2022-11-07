#!/bin/bash

poetry install
poetry export --without-hashes>requirements.txt
poetry run cyclonedx-py
