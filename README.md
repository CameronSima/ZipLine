# ZipLine

ZipLine is a simple asyncronous ASGI web framework for Python. It is designed to be simple and easy to use, while still being powerful and flexible.

## Quick Start

```python
from zipline import ZipLine

app = ZipLine()

@app.route("/")
async def home(request):
    planet = request.query.get("planet")
    return f"Hello, {planet}!"

```

```bash
uvicorn my_awesome_project:app
```

```bash
curl http://localhost:8000/?planet=Earth
```

## Handlers

a ZipLine handler is a simple `async` function that takes a `request` object and returns a response, or throws an exception.

A response can be `bytes`, `str`, `dict`, or the ZipeLine `Response` object.

If a `dict` is returned, it will be serialized to JSON.

If an `Exception` is thrown, it will be caught and handled by the framework, returning a basic error response.

## Middleware

Zipline middleware is inspired by Express.js. Any number of handler functions can be added to the middleware stack.

Each middleware function is just another ZipLine `Handler`.

Middleware functions are called in the order they are added to the stack, and pass along their context to the next handler.

The first handler in the stack to return something other than a `Request` object (including `Exception`) will short-circuit the stack and return the response.

```python
from zipline import ZipLine


# middleware functions
def auth_middleware(request):
    if request.headers.get("Authorization") == "Bearer 1234":
        is_authed = True
    else:
        is_authed = False
    return request, { "is_authed": is_authed }

def auth_guard(request, ctx):
    if not ctx.get("is_authed"):
        raise Exception("Unauthorized")


app = ZipLine()

# apply middleware to all routes
app.middleware(auth_middleware)

@app.get("/profile")
@app.middleware([auth_guard])
async def user_profile(request):
    return "Hello, World!"
```

## Dependency Injection

Like with middeleware, ZipLine supports dependency injection at the route level or application level. Dependencies are passed to the handler function as keyword arguments.

```python
from zipline import ZipLine

class LoggingService:
    def log_request(self, request):
        print(f"Request to {request.url}")

class UserService:
    def __init__(self):
        self.connection = "Connected to database"

    def get_user():
        return "User"

app = ZipLine()

# available to all routes
app.inject(LoggingService)

@app.route("/")
@app.inject(UserService, name="user_service")
async def home(request, user_service: UserService, logger: LoggingService):
    logger.log_request(request)
    return user_service.get_user()
```

## Routing

Like Express.js, ZipLine supports multiple, nested routers.

```python
from zipline import ZipLine, Router

app = ZipLine()

user_router = Router("/user")

@user_router.get("/:id")
async def get_user(request):
    return f"User {request.path_params.get('id')}"

app.router(user_router)
```
