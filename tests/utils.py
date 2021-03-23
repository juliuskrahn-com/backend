import boto3
import functools
import json


@functools.cache
def get_admin_key():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )
    string = client.get_secret_value(SecretId="blog-backend-admin-key")['SecretString']
    return json.loads(string)["blog-backend-admin-key"]
