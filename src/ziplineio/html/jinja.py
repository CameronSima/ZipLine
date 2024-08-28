import inspect
from typing import Any
from ziplineio.response import JinjaResponse
from ziplineio.utils import call_handler


def jinja(env: Any, template_name: str):
    template = env.get_template(template_name)

    def decorator(handler):
        async def wrapped_handler(req, **kwargs):
            # Pass all arguments directly to the handler
            sig = inspect.signature(handler)
            print(f"sig: {sig}")
            # Filter kwargs to only pass those that the handler expects
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            context = await call_handler(handler, req, **filtered_kwargs)
            rendered = template.render(context)
            return JinjaResponse(rendered)

        return wrapped_handler

    return decorator
