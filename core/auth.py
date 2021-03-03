import boto3
from functools import cached_property


class Auth:

    def __init__(self):
        self.current_user_is_admin = False

    @cached_property
    def admin_key(self):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name="eu-central-1"
        )
        resp = client.get_secret_value(SecretId="blog-admin-key")
        return resp['SecretString']

    def register(self, key):
        self.current_user_is_admin = key == self.admin_key
        return self.current_user_is_admin


auth = Auth()


def admin(fn):
    def wrapper(*args, **kwargs):
        if auth.current_user_is_admin:
            return fn(*args, **kwargs)
        raise PermissionError
    return wrapper
