from typing import Any

from httpx import get
from ziplineio.request_context import get_request
from ziplineio.response import JinjaResponse
from ziplineio.utils import call_handler


def jinja(env: Any, template_name: str):
    template = env.get_template(template_name)

    def decorator(handler):
        async def wrapped_handler(*args, **kwargs):
            req = get_request()
            context = await call_handler(handler, **kwargs, req=req)
            rendered = template.render(context)
            return JinjaResponse(rendered)

        return wrapped_handler

    return decorator
