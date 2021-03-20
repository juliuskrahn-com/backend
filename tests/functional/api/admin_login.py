import unittest
import requests
from tests.utils import get_admin_key
from tests.functional.api.testing_utils import base_url
import json


class TestAdminLogin(unittest.TestCase):

    def test_successful(self):
        resp = requests.post(base_url+"/admin-login", data=json.dumps({"key": get_admin_key()}))
        self.assertEqual(200, resp.status_code)

    def test_unsuccessful(self):
        resp = requests.post(base_url + "/admin-login", data=json.dumps({"key": "test"}))
        self.assertEqual(400, resp.status_code)
