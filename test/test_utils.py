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

    def test_parse_scope(self):
        scope = {
            "query_string": b"",
            "path": "/user/12",
            "headers": [(b"host", b"localhost")],
            "method": "GET",
        }
        parsed = utils.parse_scope(scope)

        # Assertions
        self.assertEqual(parsed.method, "GET")
        self.assertEqual(parsed.path, "/user/12")
        self.assertEqual(parsed.query_params, {})
        self.assertEqual(parsed.path_params, {})
        self.assertEqual(parsed.headers, {"host": "localhost"})
