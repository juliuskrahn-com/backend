import sys
import json


def get_testing_env_id():
    with open("build/deploy_testing_context.json", "r") as f:
        context = json.load(f)
        env_id = context["EnvironmentId"]
    if not env_id or type(env_id) != str:
        raise ValueError
    return env_id


if __name__ == '__main__':
    sys.stdout.write(get_testing_env_id())
