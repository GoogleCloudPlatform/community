#!/usr/bin/bash
# This is a simple utility to identify duplicate files based on the fingerprint database
# Files with the hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 are empty

DATDIR="${FIM_DATDIR:=/logs}"
cat ${DATDIR}/.base |sort -k1|uniq -w64 -c -d
