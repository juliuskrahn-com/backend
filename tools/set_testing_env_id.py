import sys
from uuid import uuid4
import json
import os


def set_testing_env_id():
    env_id = uuid4().hex
    if not os.path.exists('build'):
        os.mkdir('build')
    with open("build/deploy_testing_context.json", "w") as f:
        json.dump({"EnvironmentId": env_id}, f)
    return env_id


if __name__ == '__main__':
    sys.stdout.write(set_testing_env_id())
