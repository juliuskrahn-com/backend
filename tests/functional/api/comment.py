import unittest
from tests.functional.api.testing_utils import base_url, create_articles, delete_articles, get_admin_key
import requests
import json
import urllib.parse


# TODO avoid confusion comment/resp, http resp


class TestComment(unittest.TestCase):

    # TODO test unauthorized, name 'admin'

    def test_comment(self):
        # create, get, delete, get
        create_comment_resp = self.create_comment()
        self.assertEqual(201, create_comment_resp.status_code)
        create_comment_resp_body = create_comment_resp.json()
        self.assertIs(str, type(create_comment_resp_body.get("id")))
        comment_id = create_comment_resp_body.get("id")

        get_comments_resp = requests.get(f"{base_url}/article/{self.article['urlTitle']}/comments")
        get_comments_resp_body = get_comments_resp.json()
        for comment in get_comments_resp_body["comments"]:
            if comment["id"] == comment_id:
                self.assertEqual("test-user", comment["author"])
                self.assertEqual("awesome", comment["content"])
                break
        else:
            self.fail("Created comment not found")

        delete_comment_resp = requests.delete(
            f"{base_url}/article/{self.article['urlTitle']}/comments/{urllib.parse.quote(comment_id)}",
            data=json.dumps({"key": get_admin_key()}))
        self.assertEqual(200, delete_comment_resp.status_code)

        get_comments_deleted_resp = requests.get(f"{base_url}/article/{self.article['urlTitle']}/comments")
        get_comments_deleted_resp_body = get_comments_deleted_resp.json()
        for comment in get_comments_deleted_resp_body["comments"]:
            if comment["id"] == comment_id:
                self.fail("Deleted comment returned")

    def test_resp(self):
        # create, get, delete, get
        comment_id = self.create_comment().json()["id"]

        create_resp_http_response = requests.post(
            f"{base_url}/article/{self.article['urlTitle']}/comments/{urllib.parse.quote(comment_id)}/resps",
            data=json.dumps({
                "author": "responding-test-user",
                "content": "true"
            }))
        self.assertEqual(201, create_resp_http_response.status_code)
        create_resp_http_response_body = create_resp_http_response.json()
        resp_id = create_resp_http_response_body["id"]
        self.assertIs(str, type(resp_id))

        get_comments_http_response = requests.get(f"{base_url}/article/{self.article['urlTitle']}/comments")
        get_comments_http_response_body = get_comments_http_response.json()
        for comment in get_comments_http_response_body["comments"]:
            if comment["id"] == comment_id and resp_id in comment["resps"]:
                self.assertEqual("responding-test-user", comment["resps"][resp_id]["author"])
                self.assertEqual("true", comment["resps"][resp_id]["content"])
                break
        else:
            self.fail("Created resp not found")

        delete_resp_http_response = requests.delete(
            f"{base_url}/article/{self.article['urlTitle']}/comments/{urllib.parse.quote(comment_id)}/resps/"
            f"{urllib.parse.quote(resp_id)}",
            data=json.dumps({"key": get_admin_key()}))
        self.assertEqual(200, delete_resp_http_response.status_code)

        get_comments_deleted_http_response = requests.get(f"{base_url}/article/{self.article['urlTitle']}/comments")
        get_comments_deleted_http_response_body = get_comments_deleted_http_response.json()
        for comment in get_comments_deleted_http_response_body["comments"]:
            if comment["id"] == comment_id and resp_id in comment["resps"]:
                self.fail("Deleted resp returned")

    def create_comment(self):
        return requests.post(f"{base_url}/article/{self.article['urlTitle']}/comments", data=json.dumps({
            "author": "test-user",
            "content": "awesome"
        }))

    def setUp(self):
        self.article: dict = create_articles(n=1)[0]

    def tearDown(self):
        delete_articles([self.article])
