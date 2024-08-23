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

## Middleware

Zipline middleware is inspired by Express.js. Any number of handler functions can be added to the middleware stack. Middleware functions are called in the order they are added to the stack, and pass along their context to the next handler.

```python
from zipline import ZipLine

app = ZipLine()

def auth_middleware(request):
    if request.headers.get("Authorization") == "Bearer 1234":
        is_authed = True
    else:
        is_authed = False
    return request, { "is_authed": is_authed }

def logging_middleware(request, ctx):
    print(f"Request to {request.url}")
    print(f"Is Authed: {ctx.get('is_authed')}")
    return request

@app.middleware([auth_middleware, logging_middleware])
async def home(request):
    return "Hello, World!"
```

## Dependency Injection

ZipLine supports dependency injection at the route level or application level. Dependencies are passed to the handler function as keyword arguments.

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
from zipline import ZipLine

app = ZipLine()

user_router = ZipLine("/user")

@user_router.get("/:id")
async def get_user(request):
    return f"User {request.path_params.get('id')}"

app.router(user_router)
```
