#!/bin/bash

TOTAL=$(cat output | wc -l); ERROR1=$(grep "Error" output |  wc -l)
RATE=$((ERROR1 * 100 / TOTAL))
echo "Error rate: $ERROR1/$TOTAL (${RATE}%)"
