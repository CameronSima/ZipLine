from ziplineio.request import Request


def validate(*validators):
    def decorator(handler):
        async def wrapper(req: Request, ctx: dict):
            errors = {}
            validated_body = {}

            for validator in validators:
                validation_result = validator(req)
                validated_body.update(validation_result.get("validated", {}))
                errors.update(validation_result.get("errors", {}))

            if errors:
                return {"errors": errors}, 400

            req.body = validated_body
            return await handler(req, ctx)

        return wrapper

    return decorator


# # Example Pydantic model
# class UserModel(BaseModel):
#     username: str
#     age: int


# # Usage example with Pydantic model
# @app.post("/")
# @validate_body(BodyParam("user", UserModel))
# async def create_user_handler(req: Request, ctx: dict):
#     user = req.validated_body.get("user")
#     return {"user": user.dict()}  # Access the validated Pydantic model instance


# # Usage example with simple type validation
# @app.get("/")
# @validate_query(QueryParam("bar", str))
# async def test_handler(req: Request, ctx: dict):
#     bar = req.validated_query.get("bar")
#     return {"bar": bar}
