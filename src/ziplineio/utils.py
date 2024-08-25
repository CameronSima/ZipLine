import re
from typing import Dict
from ziplineio.models import ASGIScope, Request


def parse_scope(scope: ASGIScope) -> Request:
    query_string = scope["query_string"].decode("utf-8")

    print(f"query_string: {query_string}")

    if query_string == "":
        query_params = {}
    else:
        query_params = dict(qp.split("=") for qp in query_string.split("&"))

    split_path = scope["path"].split(":")
    if len(split_path) > 1:
        path_params = dict(zip(split_path[1:], scope["path"].split("/")[1:]))
    else:
        path_params = {}

    headers = dict((k.decode("utf-8"), v.decode("utf-8")) for k, v in scope["headers"])
    return Request(
        method=scope["method"],
        path=scope["path"],
        query_params=query_params,
        path_params=path_params,
        headers=headers,
        body="",
    )


def clean_url(path: str) -> str:
    return re.sub(r":\w+", "*", path)


def match_url_pattern(pattern: str, url: str) -> Dict[str, str]:
    """
    Match a URL against a pattern with wildcards and return a dictionary of captured parameters.

    Args:
        pattern (str): The pattern with wildcards (e.g., 'user/:id').
        url (str): The URL to match (e.g., 'users/123').

    Returns:
        Dict[str, str]: A dictionary of captured parameters (e.g., {'id': '123'}).
    """
    # Convert the pattern into a regular expression
    # Replace ':param' with '([^/]+)' to capture the parameter value
    regex_pattern = re.sub(r":(\w+)", r"(?P<\1>[^/]+)", pattern)
    regex_pattern = "^" + regex_pattern + "$"

    # Compile the regular expression
    pattern_re = re.compile(regex_pattern)

    # Match the URL against the pattern
    match = pattern_re.match(url)
    if not match:
        return {}

    # Return the captured parameters as a dictionary
    return match.groupdict()
