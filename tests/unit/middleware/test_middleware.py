import unittest
import backend.middleware as middleware
import tests.data as data
import pydantic
import json
import boto3
import functools


class TestMiddlewareCore(unittest.TestCase):

    def test_event(self):
        event = middleware.Event(data.raw_event)
        self.assertEqual(event.ressource, data.raw_event["resource"])
        self.assertEqual(event.path, data.raw_event["path"])
        self.assertEqual(event.method, data.raw_event["httpMethod"])
        self.assertEqual(event.request_context, data.raw_event["requestContext"])
        self.assertEqual(event.headers, data.raw_event["headers"])
        self.assertEqual(event.multi_value_headers, data.raw_event["multiValueHeaders"])
        self.assertEqual(event.query_string_parameters, {})
        self.assertEqual(event.multi_value_query_string_parameters, {})
        self.assertEqual(event.path_parameters, data.raw_event["pathParameters"])
        self.assertEqual(event.stage_variables, {})
        self.assertEqual(event.body, {"key": "1234", "profile": {"email": "peter@email.com"}})
        self.assertEqual(event.is_base_64_encoded, None)

        event_body_was_none = middleware.Event({"body": None})
        self.assertEqual(event_body_was_none.body, {})

    def test_response(self):
        default_response = middleware.Response()
        self.assertEqual(default_response.body, {})
        self.assertEqual(default_response.status_code, 200)
        self.assertEqual(default_response.headers, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        })
        self.assertEqual(default_response.multi_value_headers, {})
        self.assertEqual(default_response.error_messages, [])
        self.assertEqual(default_response.map(), {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"},
            "multiValueHeaders": {}
        })

        customized_response = middleware.Response(
            status_code=404,
            error_messages=["Not found"],
            body={"here": "is something else"}
        )
        self.assertEqual(customized_response.body, {"here": "is something else"})
        self.assertEqual(customized_response.status_code, 404)
        self.assertEqual(customized_response.error_messages, ["Not found"])
        self.assertEqual(customized_response.map(), {
            "statusCode": 404,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"},
            "multiValueHeaders": {},
            "body": json.dumps({
                "here": "is something else",
                "errors": ["Not found"]
            })
        })

    def test_middleware_decorator(self):
        dummy = 2

        @middleware.middleware
        def handler(event: middleware.Event, context):
            nonlocal self, dummy
            self.assertEqual(event.path, data.raw_event["path"])
            self.assertEqual(context, dummy)
            return middleware.Response()

        response = handler(data.raw_event, dummy)
        self.assertEqual(response["statusCode"], 200)


class TestMiddlewareAuthentication(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_event_wrong_admin_key = {**data.raw_event, "body": '{"key": "test"}'}
        self.raw_event_right_admin_key = {**data.raw_event,
                                          "body": json.dumps({"key": self.get_admin_key()})}

    def test_authenticator(self):
        with self.assertRaises(ValueError):
            print(middleware.authenticator.current_user_is_admin)
        admin_key = self.get_admin_key()
        middleware.authenticator.register("test")
        self.assertFalse(middleware.authenticator.current_user_is_admin)
        middleware.authenticator.register(admin_key)
        self.assertTrue(middleware.authenticator.current_user_is_admin)
        middleware.authenticator.register("test")
        self.assertFalse(middleware.authenticator.current_user_is_admin)

    def test_register_user_decorator(self):
        dummy = 2

        @middleware.register_user
        def handler(event: middleware.Event, context):
            nonlocal self, dummy
            self.assertEqual(event.path, data.raw_event["path"])
            self.assertEqual(context, dummy)
            self.assertFalse(middleware.authenticator.current_user_is_admin)

        handler(middleware.Event(self.raw_event_wrong_admin_key), dummy)

    def test_admin_guard_decorator_block(self):
        @middleware.register_user
        @middleware.admin_guard
        def handler(event: middleware.Event, context):
            self.fail("Handler executed")
        response: middleware.Response = handler(middleware.Event(self.raw_event_wrong_admin_key), None)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.error_messages, ["Requires admin key: specify the key in the request body ('key')"])

    def test_admin_guard_decorator_allow(self):
        dummy = 2

        @middleware.register_user
        @middleware.admin_guard
        def handler(event: middleware.Event, context):
            nonlocal self, dummy
            self.assertEqual(event.path, data.raw_event["path"])
            self.assertEqual(context, dummy)
            self.assertTrue(middleware.authenticator.current_user_is_admin)
            return context

        response = handler(middleware.Event(self.raw_event_right_admin_key), dummy)
        self.assertEqual(response, dummy)

    @staticmethod
    @functools.cache
    def get_admin_key():
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name="us-east-1"
        )
        return client.get_secret_value(SecretId="blog-backend-admin-key")['SecretString']

    def setUp(self):
        self.reset_authenticator()

    def tearDown(self):
        self.reset_authenticator()

    @staticmethod
    def reset_authenticator():
        middleware.authenticator._current_user_is_admin = None
        middleware.authenticator.trace = "modified"


class TestMiddlewareDataDecorator(unittest.TestCase):

    def test_data_decorator_successful(self):
        dummy = 2

        @middleware.data(self.Model)
        def handler(event: middleware.Event, context, event_data):
            self.assertEqual(event_data.key, "1234")
            self.assertEqual(event_data.profile, {"email": "peter@email.com"})
            return context

        response = handler(middleware.Event(data.raw_event), dummy)
        self.assertEqual(response, dummy)

    def test_data_decorator_unsuccessful(self):
        @middleware.data(self.Model)
        def handler(event: middleware.Event, context, event_data):
            self.fail("Handler executed")
        raw_event = {**data.raw_event, "body": '{"data": "nonsense"}'}
        response: middleware.Response = handler(middleware.Event(raw_event), None)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.error_messages[0][0], "Request validation failed (pydantic error)")

    class Model(pydantic.BaseModel):
        key: str
        profile: dict

        @classmethod
        def build(cls, event: middleware.Event, context):
            return cls(key=event.body.get("key"), profile=event.body.get("profile"))
