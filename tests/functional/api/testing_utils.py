import os
import requests
import json
from tests.utils import get_admin_key
from tests.functional.api.testing_data import generate_article_data
from typing import List
import logging


environment = os.environ.get("Environment")

if environment == "Testing":
    logging.info("Test Testing Environment Endpoints")
    base_url = "https://testing.api.juliuskrahn.com"
else:
    logging.info("Test Production Environment Endpoints")
    base_url = "https://api.juliuskrahn.com"


def create_articles(overwrite=None, n=3):
    if overwrite is None:
        overwrite = {}
    articles = []
    for i in range(n):
        articles.append({**generate_article_data(), **overwrite})
        requests.post(base_url + "/article", data=json.dumps({**articles[i], "key": get_admin_key()}))
    return articles


def delete_articles(articles: List[dict]):
    for article in articles:
        requests.delete(base_url + "/article/" + article["urlTitle"],
                        data=json.dumps({"key": get_admin_key()}))