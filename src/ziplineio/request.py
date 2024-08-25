from typing import Dict


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query_params: Dict[str, str] = {},
        path_params: Dict[str, str] = {},
        headers: Dict[str, str] = {},
        body: str = "",
    ):
        self.method = method
        self.path = path
        self.path_params = path_params
        self.query_params = query_params
        self.headers = headers
        self.body = body

    method: str
    path: str
    query_params: Dict[str, str]
    path_params: Dict[str, str]
    headers: Dict[str, str]
    body: str
