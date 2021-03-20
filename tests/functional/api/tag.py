import unittest
from tests.functional.api.testing_utils import base_url, create_articles, delete_articles
import requests
from uuid import uuid4


class TestTag(unittest.TestCase):

    def test_tag_article_collection(self):
        resp = requests.get(base_url + "/tag/" + self.tag)
        resp_articles = resp.json()["articles"]
        self.assertTrue(self.articles)
        for article in resp_articles:
            i = 0
            for generated_article in self.articles:
                if article["urlTitle"] == generated_article["urlTitle"]:
                    self.articles.pop(i)
                    break
                i += 1
        self.assertFalse(self.articles)

    def test_tag_collection(self):
        resp = requests.get(base_url + "/tag/")
        resp_tags = resp.json()["tags"]
        self.assertIn(self.tag, resp_tags)

    def setUp(self):
        self.tag = uuid4().hex
        self.articles = create_articles({"tag": self.tag})

    def tearDown(self):
        self.tag = uuid4().hex
        delete_articles(self.articles)
