from . import Response, Event
import functools
from typing import Callable
from pydantic import ValidationError
import boto3
import os
import logging


class Authenticator:
    """Loads the admin key once - compares against that key and stores the status of the current user

    Used as a global instance, the user is registered by the "register_user" decorator
    """

    def __init__(self):
        self._current_user_is_admin = None

    @functools.cached_property
    def _admin_key(self):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name="us-east-1"
        )
        resp = client.get_secret_value(SecretId="blog-backend-admin-key")
        return resp['SecretString']

    def register(self, key):
        """Sets the admin status (bool) of the current user by comparing the user's key"""
        self._current_user_is_admin = key and key == self._admin_key
        return self._current_user_is_admin

    @property
    def current_user_is_admin(self):
        if self._current_user_is_admin is None:
            raise ValueError("User hasn't been registered")
        return self._current_user_is_admin


authenticator = Authenticator()


# handler decorator
def register_user(middleware_wrapped_handler: Callable):
    """Registers the user on the "authenticator" global"""
    @functools.wraps(middleware_wrapped_handler)
    def wrapper(*args, **kwargs):
        key = False
        if type(args[0].body) == dict:
            key = args[0].body.get("key", False)
        authenticator.register(key)
        return middleware_wrapped_handler(*args, **kwargs)
    return wrapper


# handler decorator
def admin_guard(middleware_wrapped_handler: Callable):
    """Executes the handler if the user is admin, otherwise a 401 status code is returned along with an error message

    The user has to be registered, use the "register_user" decorator
    """

    @functools.wraps(middleware_wrapped_handler)
    def wrapper(*args, **kwargs):
        if authenticator.current_user_is_admin:
            return middleware_wrapped_handler(*args, **kwargs)
        return Response(
            status_code=401,
            error_messages=["Requires admin key: specify the key in the request body ('key')"])
    return wrapper


# handler decorator
def data(model):
    """Parses Lambda event and context with the pydantic model and passes it on to the handler

    If validation fails a 400 status code is returned along with an error message (including pydantic's error).
    Style: model attributes in camelCase
    """

    def decorator(middleware_wrapped_handler: Callable):
        @functools.wraps(middleware_wrapped_handler)
        def wrapper(*args, **kwargs):
            try:
                data_ = model.build(args[0], args[1])
            except ValidationError as e:
                return Response(
                    status_code=400,
                    error_messages=[["Request validation failed (pydantic error)", e.json()]])
            except:
                logging.exception("Data Model failed to build, return 500 resp.")
                return Response(
                    status_code=500,
                    error_messages=["Failed to load the request data. Make sure to check you request."])
            return middleware_wrapped_handler(*args, data_, **kwargs)
        return wrapper
    return decorator


def wrap_boto3_dynamodb_table(table):
    """Wraps a boto3 dynamodb table to provide some utils

    table = wrap_boto3_dynamodb_table(boto3.resource("dynamodb").Table("my-table"))
    """

    def ignore_empty_pagination_key_wrapper(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if "ExclusiveStartKey" in kwargs and kwargs["ExclusiveStartKey"] is None:
                del kwargs["ExclusiveStartKey"]
            return fn(*args, **kwargs)
        return wrapper

    def paginate_items_wrapper(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            items = []
            key = None
            while True:
                response = fn(*args, **kwargs, ExclusiveStartKey=key)
                if "Items" in response:
                    items += response["Items"]
                if "LastEvaluatedKey" in response:
                    key = response["LastEvaluatedKey"]
                    continue
                break
            return items
        return wrapper

    table.scan = ignore_empty_pagination_key_wrapper(table.scan)
    table.query = ignore_empty_pagination_key_wrapper(table.query)
    table.scan_paginate_items = paginate_items_wrapper(table.scan)
    table.query_paginate_items = paginate_items_wrapper(table.query)
    return table


def get_article_table():
    name = os.environ.get("ArticleTableName")
    return wrap_boto3_dynamodb_table(boto3.resource("dynamodb").Table(name))


def get_comment_table():
    name = os.environ.get("CommentTableName")
    return wrap_boto3_dynamodb_table(boto3.resource("dynamodb").Table(name))
