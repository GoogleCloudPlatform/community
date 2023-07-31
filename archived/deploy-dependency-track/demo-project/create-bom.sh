#!/bin/bash

poetry install
poetry run cyclonedx-py --format xml --poetry --force
