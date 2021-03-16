from . import Response, Event, authenticator
import functools
from typing import Callable
from pydantic import ValidationError
import boto3


def admin_guard(middleware_wrapped_handler: Callable):
    """Executes the handler if the user is admin, otherwise a 401 status code is returned along with an error message"""

    @functools.wraps(middleware_wrapped_handler)
    def wrapper(event: Event, context):
        if authenticator.current_user_is_admin:
            return middleware_wrapped_handler(event, context)
        return Response(
            status_code=401,
            error_messages=["Requires admin key: specify the key in the request body ('key')"])

    return wrapper


def data(model):
    """Parses Lambda event and context with the pydantic model and passes it on to the handler

    If validation fails a 400 status code is returned along with an error message (including pydantic's error).
    Style: model attributes in camelCase
    """

    def decorator(middleware_wrapped_handler: Callable):
        @functools.wraps(middleware_wrapped_handler)
        def wrapper(event: Event, context):
            try:
                data_ = model.build(event, context)
                return middleware_wrapped_handler(event, context, data_)
            except ValidationError as e:
                return Response(
                    status_code=400,
                    error_messages=[["Request validation failed", e.json()]])
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
                if "items" in response:
                    items += response["items"]
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
    return wrap_boto3_dynamodb_table(boto3.resource("dynamodb").Table("blog-article"))


def get_comment_table():
    return wrap_boto3_dynamodb_table(boto3.resource("dynamodb").Table("blog-comment"))
