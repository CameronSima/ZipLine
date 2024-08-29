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

Middleware can be can be applied at the application, router, or individual route level.

```python
from zipline import ZipLine, Router, middleware


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

def is_user_guard(request, ctx):
    if ctx.get("user_id") != request.path_params.get("id"):
        raise Exception("Forbidden")


app = ZipLine()


# apply middleware to all routes
app.middleware([auth_middleware])

user_router = Router("/user")

# apply middleware at the router-level
user_router.middleware([auth_guard])

@app.get("/profile")
@middleware([is_user_guard]) # apply middleware to one router
async def user_profile(request):
    return "Hello, World!"
```

## Dependency Injection

Like with middeleware, ZipLine supports dependency injection at the route, router, or application level. In addition, dependencies can be injected into other dependencies. Dependencies are passed to the handler function as keyword arguments.

```python
from zipline import ZipLine, inject

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
@inject(UserService, name="user_service")
async def home(request, user_service: UserService, logger: LoggingService):
    logger.log_request(request)
    return user_service.get_user()
```

Services can be any class, but Zipline includes a special `Service` class. Classes that inherit from `Service` have the ability to access all other services in their scope.

Classes that inherit from `Service` are expected to have a property `name` attribute, which is used to identify the service in the dependency injection container. Otherwise, they can be referenced by their class name (like with the `@inject` decorator).

```python
from zipline import ZipLine, Service

class LoggingService(Service):
    def __init__(self):
        self.name = "logger"

    def error(self, message):
        print(f"Error! {message}")

class DBService(Service):
    def __init__(self, logger: LoggingService):
        self.name = "db_service"

    def get_connection(self):
        try:
            return db.connect()
        except Exception as e:
            self.logger.error(e)

class UserService(Service):
    def __init__(self, db_service: DBService, logger: LoggingService):
        self.name = "user_service"

    def get_user(id: str):
        conn = self.db_service.get_connection()
         try:
            return conn.query("SELECT * FROM users WHERE id = ?", id)
        except Exception as e:
            self.logger.error(f"User {id} not found")


app = ZipLine()
# inject all services; order doesn't matter
app.inject([LoggingService, DBService, UserService])

@app.route("/user/:id")
async def get_user(request):
    user_id = request.path_params.get("id")
    return user_service.get_user(user_id)
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

## Static Files

ZipLine can serve static files from a directory.

```python
from zipline import ZipLine


app = ZipLine()

# path_prefix is optional; defaults to "/static"
app.static("test/mocks/static", path_prefix="/my_static_url")
```

## HTML Templates

ZipLine can render HTML templates using Jinja2.

The `jinja` decorator takes a Jinja2 `Environment` object and a template name to be rendered by the handler. Rather than a regular response, the handler should return a dictionary of context variables to be passed to the template.

```python
from jinja2 import Environment, PackageLoader, select_autoescape
from ziplineio. import ZipLine
from ziplineio.html.jinja import jinja

env = Environment(loader=PackageLoader("myapp"), autoescape=select_autoescape())

app = ZipLine()
app.static("static_files")

@app.get("/")
@jinja(env, "home.html")
def home(req):
    return {"message": "Hello, world!"}
```
