from functools import wraps
from ziplineio.request import Request
from pydantic import ValidationError

from ziplineio.validation.query import QueryParam


class BodyParam(QueryParam):
    """Alias Query param."""

    pass


def validate_body(*body_params):
    """
    Decorator to validate body parameters.
    """

    def decorator(handler):
        @wraps(handler)
        async def wrapper(req: Request, *args, **kwargs):
            body = req.body.json()
            errors = {}
            validated_body = {}

            for param in body_params:
                param_name = param.param
                value = body.get(param_name)
                if value is None:
                    if param.required:
                        errors[param_name] = "Missing required body parameter"
                else:
                    try:
                        validated_body[param_name] = param.validate(value)
                    except (ValueError, ValidationError) as e:
                        errors[param_name] = str(e)

            if errors:
                return {"errors": errors}, 400

            # Attach validated body parameters to the request
            req.body = validated_body
            return await handler(req, *args, **kwargs)

        return wrapper

    return decorator if body_params else lambda req: decorator(lambda *_: None)(req)
