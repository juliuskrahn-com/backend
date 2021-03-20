import unittest
from tests.functional.api.testing_utils import base_url, create_articles, delete_articles
import requests


class TestArticleCollection(unittest.TestCase):

    def test(self):
        resp = requests.get(base_url+"/article")
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

    def setUp(self):
        self.articles = create_articles()

    def tearDown(self):
        delete_articles(self.articles)
