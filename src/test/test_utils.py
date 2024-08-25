import unittest
from ziplineio import utils


class TestUtils(unittest.TestCase):
    def test_clean_url(self):
        url = "/user/:id"
        parsed = utils.clean_url(url)

        # Assertions
        self.assertEqual(parsed, "/user/*")

    def test_match_url_pattern(self):
        pattern = "/user/:id"
        url = "/user/123"
        parsed = utils.match_url_pattern(pattern, url)

        # Assertions
        self.assertEqual(parsed, {"id": "123"})
