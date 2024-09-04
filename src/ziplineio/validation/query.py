from functools import wraps
import inspect
from typing import Type, Union
from pydantic import BaseModel, ValidationError
from ziplineio.request import Request


class QueryParam:
    def __init__(
        self, param: str, type: Union[Type, BaseModel] = str, required: bool = True
    ):
        self.param = param
        self.type = type
        self.required = required

    def validate(self, value):
        if isinstance(self.type, type) and issubclass(self.type, BaseModel):
            try:
                # Use Pydantic model for validation
                model_instance = self.type.parse_obj(value)
                return model_instance
            except ValidationError as e:
                raise ValueError(f"Validation error for {self.param}: {e}")

        try:
            # Basic type casting
            return self.type(value)
        except ValueError:
            raise ValueError(
                f"Invalid type for {self.param}, expected {self.type.__name__}"
            )


def validate_query(*query_params):
    """
    Decorator to validate query parameters.
    """

    def decorator(handler):
        # Use inspect to get the function signature and find the request parameter name
        signature = inspect.signature(handler)
        request_param_name = None

        # Find the parameter annotated with the Request type
        for param_name, param in signature.parameters.items():
            if param.annotation == Request or isinstance(
                param_name, Request
            ):  # Look for the parameter with type `Request`
                request_param_name = param_name
                break

        print("request_param_name", request_param_name)

        if request_param_name is None:
            raise ValueError(
                "Handler function must have a parameter of type `Request`."
            )

        @wraps(handler)
        async def wrapper(*args, **kwargs):
            # print("req", req)
            print("args", args)

            print("kwargs", kwargs)

            req = kwargs.get(request_param_name)

            errors = {}
            validated_query = {}

            for param in query_params:
                param_name = param.param
                value = req.query_params.get(param_name)
                if value is None:
                    if param.required:
                        errors[param_name] = "Missing required query parameter"
                else:
                    try:
                        validated_query[param_name] = param.validate(value)
                    except (ValueError, ValidationError) as e:
                        errors[param_name] = str(e)

            if errors:
                return {"errors": errors}, 400

            # Attach validated query parameters to the request
            req.query_params = validated_query

            return await handler(*args, **kwargs)

        return wrapper

    return decorator if query_params else lambda req: decorator(lambda *_: None)(req)
