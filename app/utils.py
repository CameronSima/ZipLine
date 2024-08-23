import re
from app.models import ASGIScope, Request


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


def clean_path(path: str) -> str:
    return re.sub(r":\w+", "*", path)
