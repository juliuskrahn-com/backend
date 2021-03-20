import unittest
import requests
from tests.utils import get_admin_key
from tests.functional.api.testing_data import generate_article_data
from tests.functional.api.testing_utils import base_url
import json
from uuid import uuid4


class TestArticle(unittest.TestCase):

    def test_authorized_workflow(self):
        # create, get, update, get, delete, get

        create_article_data = generate_article_data()
        create_article_data["key"] = get_admin_key()

        create_article_resp = requests.post(base_url + "/article", data=json.dumps(create_article_data))
        self.assertEqual(201, create_article_resp.status_code)

        get_article_resp = requests.get(base_url + "/article/" + create_article_data["urlTitle"])
        self.assertEqual(200, get_article_resp.status_code)
        get_article = get_article_resp.json()["article"]
        self.assertEqual(create_article_data["urlTitle"], get_article["urlTitle"])
        self.assertEqual(create_article_data["title"], get_article["title"])
        self.assertEqual(create_article_data["tag"], get_article["tag"])
        self.assertEqual(create_article_data["description"], get_article["description"])
        self.assertEqual(create_article_data["content"], get_article["content"])
        self.assertEqual(str, type(get_article["published"]))

        update_article_data = generate_article_data()
        update_article_data["key"] = get_admin_key()
        update_article_resp = requests.patch(base_url + "/article/" + create_article_data["urlTitle"],
                                             data=json.dumps(update_article_data))
        self.assertEqual(200, update_article_resp.status_code)

        get_updated_article_resp = requests.get(base_url + "/article/" + create_article_data["urlTitle"])
        self.assertEqual(200, get_updated_article_resp.status_code)
        get_updated_article = get_article_resp.json()["article"]
        self.assertEqual(create_article_data["urlTitle"], get_updated_article["urlTitle"])
        self.assertEqual(create_article_data["title"], get_updated_article["title"])
        self.assertEqual(create_article_data["tag"], get_updated_article["tag"])
        self.assertEqual(create_article_data["description"], get_updated_article["description"])
        self.assertEqual(create_article_data["content"], get_updated_article["content"])
        self.assertEqual(get_article["published"], get_updated_article["published"])

        delete_article_resp = requests.delete(base_url + "/article/" + create_article_data["urlTitle"],
                                              data=json.dumps({"key": get_admin_key()}))
        self.assertEqual(200, delete_article_resp.status_code)

        get_deleted_article_resp = requests.get(base_url + "/article/" + create_article_data["urlTitle"])
        self.assertEqual(404, get_deleted_article_resp.status_code)

    def test_unauthorized_workflow(self):
        # create article, update already created article, delete already created article

        article = generate_article_data()

        create_article_resp = requests.post(base_url + "/article", data=json.dumps(article))
        self.assertEqual(401, create_article_resp.status_code)

        _create_article_resp = requests.post(base_url + "/article", data=json.dumps({
            **article,
            "key": get_admin_key()
        }))

        update_article_resp = requests.patch(base_url + "/article/" + article["urlTitle"],
                                             data=json.dumps(article))
        self.assertEqual(401, update_article_resp.status_code)

        update_article_with_wrong_key_resp = requests.patch(base_url + "/article/" + article["urlTitle"],
                                                            data=json.dumps({
                                                                **article,
                                                                "key": "test"
                                                            }))
        self.assertEqual(401, update_article_with_wrong_key_resp.status_code)

        delete_article_resp = requests.delete(base_url + "/article/" + article["urlTitle"])
        self.assertEqual(401, delete_article_resp.status_code)

        delete_article_with_wrong_key_resp = requests.delete(base_url + "/article/" + article["urlTitle"],
                                                             data=json.dumps({"key": "test"}))
        self.assertEqual(401, delete_article_with_wrong_key_resp.status_code)

    def test_delete_non_existing_article(self):
        delete_article_resp = requests.delete(base_url + "/article/" + uuid4().hex,
                                              data=json.dumps({"key": get_admin_key()}))
        self.assertEqual(200, delete_article_resp.status_code)

    def update_non_existing_article(self):
        update_article_resp = requests.patch(base_url + "/article/" + uuid4().hex, data=json.dumps({
            **generate_article_data(),
            "key": get_admin_key()
        }))
        self.assertEqual(404, update_article_resp.status_code)
