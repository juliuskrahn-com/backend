import json
import functools
from typing import Optional, Callable


class Event:
    """Mapped API Gateway event"""

    def __init__(self, event: dict):
        self.ressource: str = event.get("resource")
        self.path: str = event.get("path")
        self.method: str = event.get("httpMethod")
        self.headers: dict = event.get("headers", {})
        self.multi_value_headers: dict = event.get("multiValueHeaders", {})
        self.query_string_parameters: dict = event.get("queryStringParameters", {})
        self.multi_value_query_string_parameters: dict = event.get("multiValueQueryStringParameters", {})
        self.path_parameters: dict = event.get("pathParameters", {})
        self.stage_variables: dict = event.get("stageVariables", {})
        self.request_context: dict = event.get("requestContext", {})
        self.body: dict = json.loads(event.get("body", ""))
        self.is_base_64_encoded: bool = event.get("isBase64Encoded", False)


# TODO mapping for Lambda context


class Response:
    """Response data (providing some utilities/ defaults) that can be mapped to the format expected by API Gateway

    CORS enabled by default (can be overwritten)
    """

    def __init__(self,
                 status_code: int = 200,
                 headers: Optional[dict] = None,
                 multi_value_headers: Optional[dict] = None,
                 body: Optional[dict] = None,
                 error_messages: Optional[list] = None):
        self.status_code = status_code
        self.headers = headers if headers else {}
        if "Access-Control-Allow-Origin" not in self.headers:
            self.headers["Access-Control-Allow-Origin"] = "*"
        if "Access-Control-Allow-Methods" not in self.headers:
            self.headers["Access-Control-Allow-Methods"] = "*"
        if "Access-Control-Allow-Headers" not in self.headers:
            self.headers["Access-Control-Allow-Headers"] = "*"
        self.multi_value_headers = multi_value_headers if multi_value_headers else {}
        self.body = body if body else {}
        self.error_messages = error_messages if error_messages else []

    def map(self):
        """Maps the response to the format expected by API Gateway"""
        body = {
            **self.body
        }
        if self.error_messages:
            body["errors"] = self.error_messages
        return {
            "statusCode": self.status_code,
            "headers": self.headers,
            "multiValueHeaders": self.multi_value_headers,
            "body": json.dumps(body)
        }


def middleware(handler: Callable):
    """Middleware between API Gateway and a handler: maps event/ response

    The handler gets a mapped event and an unmodified context; and has to return a Response"""

    @functools.wraps(handler)
    def wrapper(event: dict, context: dict):
        event = Event(event)
        response: Response = handler(event, context)
        return response.map()
    return wrapper
