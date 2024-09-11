import re
import inspect
import asyncio

from typing import Dict


from ziplineio.request import Request
from ziplineio.response import Response
from ziplineio.handler import Handler
from ziplineio.models import ASGIScope


"""
Only pass the kwargs that are required by the handler function.
"""


def clean_kwargs(kwargs: dict, handler: Handler) -> dict:
    params = inspect.signature(handler).parameters
    kwargs = {k: v for k, v in kwargs.items() if k in params}
    return kwargs


async def call_handler(
    handler: Handler,
    **kwargs,
) -> bytes | str | dict | Response | Exception:
    try:
        kwargs = clean_kwargs(kwargs, handler)
        if not inspect.iscoroutinefunction(handler):
            response = await asyncio.to_thread(handler, **kwargs)
        else:
            response = await handler(**kwargs)

    except Exception as e:
        response = e

    return response


def parse_scope(scope: ASGIScope) -> Request:
    query_string = scope["query_string"].decode("utf-8")

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
