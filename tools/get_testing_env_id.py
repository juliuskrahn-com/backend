import sys
import json
import logging


def get_testing_env_id():
    fp = "build/deploy_testing_context.json"
    try:
        with open(fp, "r") as f:
            context = json.load(f)
            env_id = context["EnvironmentId"]
        if not env_id or type(env_id) != str:
            raise ValueError(f"Testing environment id set in file: '{fp}' is invalid.")
    except FileNotFoundError:
        logging.warning(f"Testing environment id is now set to an empty string, "
                        f"because file: '{fp}' wasn't found.")
        env_id = ""
    return env_id


if __name__ == '__main__':
    sys.stdout.write(get_testing_env_id())
