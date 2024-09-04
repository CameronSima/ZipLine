import unittest

from pydantic import BaseModel


from ziplineio.app import App

from ziplineio.request import Request

from ziplineio.utils import call_handler
from ziplineio.validation.body import BodyParam, validate_body
from ziplineio.validation.query import QueryParam, validate_query


class TestValidateBody(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

    async def test_validate_simple_body_params(self):
        @self.app.post("/")
        @validate_body(BodyParam("username", str), BodyParam("age", float))
        async def create_user_handler(req: Request):
            username = req.body.get("username")
            age = req.body.get("age")
            return {"username": username, "age": age}

        req = Request(method="POST", path="/", body={"username": "Amy", "age": 0.11})
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response["username"], "Amy")
        self.assertEqual(response["age"], 0.11)

    async def test_validate_pydantic_body_params(self):
        # # Example Pydantic model
        class UserModel(BaseModel):
            username: str
            age: int

        @self.app.post("/")
        @validate_body(BodyParam("user", UserModel))
        async def create_user_handler(req: Request):
            user = req.body.get("user")
            return {
                "user": user.model_dump()
            }  # Access the validated Pydantic model instance

        req = Request(
            method="POST", path="/", body={"user": {"username": "John", "age": 30}}
        )
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response["user"], {"username": "John", "age": 30})

    async def test_validate_missing_required_body_params(self):
        @self.app.post("/")
        @validate_body(BodyParam("username", str), BodyParam("age", float))
        async def create_user_handler(req: Request):
            username = req.body.get("username")
            age = req.body.get("age")
            return {"username": username, "age": age}

        req = Request(method="POST", path="/", body={"username": "Amy"})
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(
            response, ({"errors": {"age": "Missing required body parameter"}}, 400)
        )

    async def test_validate_missing_optional_body_params(self):
        @self.app.post("/")
        @validate_body(
            BodyParam("username", str, required=False), BodyParam("age", float)
        )
        async def create_user_handler(req: Request):
            username = req.body.get("username")
            age = req.body.get("age")
            return {"username": username, "age": age}

        req = Request(method="POST", path="/", body={"age": 0.11})
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response, {"username": None, "age": 0.11})

    async def test_validate_invalid_body_params(self):
        @self.app.post("/")
        @validate_body(BodyParam("username", str), BodyParam("age", float))
        async def create_user_handler(req: Request):
            username = req.body.get("username")
            age = req.body.get("age")
            return {"username": username, "age": age}

        req = Request(
            method="POST", path="/", body={"username": "Amy", "age": "invalid"}
        )
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(
            response,
            (
                {"errors": {"age": "Invalid type for age, expected float"}},
                400,
            ),
        )


class TestValidateQuery(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Initialize the app
        self.app = App()

    async def test_validate_simple_query_params(self):
        @self.app.get("/")
        @validate_query(QueryParam("username", str), QueryParam("age", float))
        async def create_user_handler(req: Request):
            username = req.query_params.get("username")
            age = req.query_params.get("age")
            return {"username": username, "age": age}

        req = Request(
            method="GET", path="/", query_params={"username": "Amy", "age": 0.11}
        )
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response["username"], "Amy")
        self.assertEqual(response["age"], 0.11)

    async def test_validate_pydantic_query_params(self):
        # # Example Pydantic model
        class UserModel(BaseModel):
            username: str
            age: int

        @self.app.get("/")
        @validate_query(QueryParam("user", UserModel))
        async def create_user_handler(req: Request):
            user = req.query_params.get("user")
            return {"user": user.model_dump()}

        req = Request(
            method="GET",
            path="/",
            query_params={"user": {"username": "John", "age": 30}},
        )
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response["user"], {"username": "John", "age": 30})

    async def test_validate_missing_required_query_params(self):
        @self.app.get("/")
        @validate_query(QueryParam("username", str), QueryParam("age", float))
        async def create_user_handler(req: Request):
            username = req.query_params.get("username")
            age = req.query_params.get("age")
            return {"username": username, "age": age}

        req = Request(method="GET", path="/", query_params={"username": "Amy"})
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(
            response, ({"errors": {"age": "Missing required query parameter"}}, 400)
        )

    async def test_validate_missing_optional_query_params(self):
        @self.app.get("/")
        @validate_query(
            QueryParam("username", str, required=False), QueryParam("age", float)
        )
        async def create_user_handler(req: Request):
            username = req.query_params.get("username")
            age = req.query_params.get("age")
            return {"username": username, "age": age}

        req = Request(method="GET", path="/", query_params={"age": 0.11})
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(response, {"username": None, "age": 0.11})

    async def test_validate_invalid_query_params(self):
        @self.app.get("/")
        @validate_query(QueryParam("username", str), QueryParam("age", float))
        async def create_user_handler(req: Request):
            username = req.query_params.get("username")
            age = req.query_params.get("age")
            return {"username": username, "age": age}

        req = Request(
            method="GET", path="/", query_params={"username": "Amy", "age": "invalid"}
        )
        response = await call_handler(create_user_handler, req=req)

        self.assertEqual(
            response,
            (
                {"errors": {"age": "Invalid type for age, expected float"}},
                400,
            ),
        )
