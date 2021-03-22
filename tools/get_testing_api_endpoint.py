import sys
import json
from get_testing_env_id import get_testing_env_id


def get_testing_env_api_endpoint():
    testing_env_id = get_testing_env_id()
    with open("build/deploy_testing_output.json") as f:
        output = json.load(f)
        endpoint = output["Testing" + testing_env_id]["ApiIEndpoint"]
    return endpoint


if __name__ == '__main__':
    sys.stdout.write(get_testing_env_api_endpoint())
