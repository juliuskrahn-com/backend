#!/bin/bash
# run in project root dir

env_id="$(python tools/get_testing_env_id.py)"

cdk destroy "Testing${env_id}" --force
