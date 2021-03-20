import boto3
import functools


@functools.cache
def get_admin_key():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )
    return client.get_secret_value(SecretId="blog-backend-admin-key")['SecretString']
