from typing import Any

from ziplineio.response import JinjaResponse
from ziplineio.utils import call_handler


def jinja(env: Any, template_name: str):
    template = env.get_template(template_name)

    def decorator(handler):
        async def wrapped_handler(*args, **kwargs):
            context = await call_handler(handler, *args, **kwargs, format=False)
            rendered = template.render(context)
            return JinjaResponse(rendered)

        return wrapped_handler

    return decorator
