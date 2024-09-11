from contextvars import ContextVar

from ziplineio.request import Request

_request_context_var = ContextVar("request_context")


def set_request(request: Request):
    _request_context_var.set(request)


def get_request() -> Request:
    return _request_context_var.get()
