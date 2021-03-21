#!/bin/bash
# run in project root dir

env_id="$(python tools/set_testing_env_id.py)"

npx cdk deploy "Testing${env_id}" --require-approval=never --outputs-file build/deploy_testing_output.json
