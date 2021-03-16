import boto3
import functools


class Authenticator:
    """Loads the admin key once - compares against that key and stores the status of the current user

    Used as a global instance, the user is registered by the middleware decorator.
    """

    def __init__(self):
        self.current_user_is_admin = False

    @functools.cached_property
    def _admin_key(self):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name="us-east-1"
        )
        resp = client.get_secret_value(SecretId="blog-admin-key")
        return resp['SecretString']

    def register(self, key):
        """Sets the admin status (bool) of the current user by comparing the user's key"""
        self.current_user_is_admin = key == self._admin_key
        return self.current_user_is_admin
