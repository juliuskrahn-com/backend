import unittest
import requests
from tests.functional.api.testing_utils import base_url
from uuid import uuid4


class TestCatchAll(unittest.TestCase):

    def test_root(self):
        resp = requests.get(base_url)
        self.assertEqual(404, resp.status_code)

    # TODO test fails
    # def test_sub_path(self):
    #     resp = requests.get(base_url+"/"+uuid4().hex)
    #     self.assertEqual(404, resp.status_code)
