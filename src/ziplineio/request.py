from calendar import c
import json
from typing import Dict


class Body:
    body: bytes

    def __init__(self, body: bytes):
        self.body = body

    def get(self, key: str):
        return self.json().get(key)

    def json(self) -> Dict:
        return json.loads(self.body.decode("utf-8"))

    def __str__(self):
        return self.body.decode("utf-8")

    def bytes(self):
        return self.body

    @classmethod
    def from_json(cls, data: Dict):
        return cls(json.dumps(data).encode("utf-8"))

    @classmethod
    def from_str(cls, data: str):
        return cls(data.encode("utf-8"))

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(data)


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        query_params: Dict[str, str] = {},
        path_params: Dict[str, str] = {},
        headers: Dict[str, str] = {},
        body: Body = Body(b""),
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
    body: Body
