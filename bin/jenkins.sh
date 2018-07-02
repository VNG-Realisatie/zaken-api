#!/bin/bash

set -e  # exit on errors
set -x  # echo commands

if [[ -z "$WORKSPACE" ]]; then
    export WORKSPACE=$(pwd)
fi

docker-compose -p zrc_tests -f ./docker-compose.yml build tests
docker-compose -p zrc_tests -f ./docker-compose.yml run tests
