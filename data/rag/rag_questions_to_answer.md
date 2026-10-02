## r00 (factual)
**Q:** Can I set headers and cookies through a Response parameter inside a dependency?

**Gold passage (fastapi/advanced/response-headers#000):**

FastAPI > Response Headers > Use a `Response` parameter

You can declare a parameter of type `Response` in your *path operation function* (as you can do for cookies).

And then you can set headers in that *temporal* response object.

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/headers-and-object/")
def get_headers(response: Response):
    response.headers["X-Cat-Dog"] = "alone in the world"
    return {"message": "Hello World"}
```

And then you can return any object you need, as you normally would (a `dict`, a database model, etc).

And if you declared a `response_model`, it will still be used to filter and convert the object you returned.

**FastAPI** will use that *temporal* response to extract the headers (also cookies and status code), and will put them in the final response that contains the value you returned, filtered by any `response_model`.

You can also declare the `Response` parameter in dependencies, and set headers (and cookies) in them.

---

## r01 (how-to)
**Q:** How do I validate a list of TypedDict users with a TypeAdapter?

**Gold passage (pydantic/concepts/type_adapter#001):**

Pydantic > Type Adapter

```python
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError

class User(TypedDict):
    name: str
    id: int

user_list_adapter = TypeAdapter(list[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))
#> [{'name': 'Fred', 'id': 3}]

try:
    user_list_adapter.validate_python(
        [{'name': 'Fred', 'id': 'wrong', 'other': 'no'}]
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for list[User]
    0.id
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='wrong', input_type=str]
    """

print(repr(user_list_adapter.dump_json(user_list)))
#> b'[{"name":"Fred","id":3}]'
```

---

## r02 (comparison)
**Q:** Why does the tutorial strongly encourage running and editing the examples in my own editor?

**Gold passage (fastapi/tutorial/index#005):**

FastAPI > Tutorial - User Guide > Run the code

```console
     <font color="#D3D7CF"> INFO </font>  Waiting for application startup.
     <font color="#D3D7CF"> INFO </font>  Application startup complete.
```

It is **HIGHLY encouraged** that you write or copy the code, edit it and run it locally.

Using it in your editor is what really shows you the benefits of FastAPI, seeing how little code you have to write, all the type checks, autocompletion, etc.

---

---

## r03 (factual)
**Q:** Which large companies are quoted as using FastAPI for ML services or open source frameworks?

**Gold passage (fastapi/index#002):**

FastAPI > FastAPI > Sponsors

{% if sponsors %}
{% for sponsor in sponsors.gold -%}

{% endfor -%}
{%- for sponsor in sponsors.silver -%}

{% endfor %}
{% endif %}

Other sponsors

## Opinions

"_[...] I'm using **FastAPI** a ton these days. [...] I'm actually planning to use it for all of my team's **ML services at Microsoft**. Some of them are getting integrated into the core **Windows** product and some **Office** products._"

Kabir Khan - Microsoft (ref)

---

"_We adopted the **FastAPI** library to spawn a **REST** server that can be queried to obtain **predictions**. [for Ludwig]_"

Piero Molino, Yaroslav Dudin, and Sai Sumanth Miryala - Uber (ref)

---

"_**Netflix** is pleased to announce the open-source release of our **crisis management** orchestration framework: **Dispatch**! [built with **FastAPI**]_"

Kevin Glisson, Marc Vilanova, Forest Monsen - Netflix (ref)

---

---

## r04 (how-to)
**Q:** How do I declare positional-only and keyword-only parameters in a function decorated with validate_call?

**Gold passage (pydantic/concepts/validation_decorator#004):**

Pydantic > Validation Decorator > Function signatures

```python
from pydantic import validate_call

@validate_call
def pos_or_kw(a: int, b: int = 2) -> str:
    return f'a={a} b={b}'

print(pos_or_kw(1, b=3))
#> a=1 b=3

@validate_call
def kw_only(*, a: int, b: int = 2) -> str:
    return f'a={a} b={b}'

print(kw_only(a=1))
#> a=1 b=2
print(kw_only(a=1, b=3))
#> a=1 b=3

@validate_call
def pos_only(a: int, b: int = 2, /) -> str:
    return f'a={a} b={b}'

print(pos_only(1))
#> a=1 b=2

@validate_call
def var_args(*args: int) -> str:
    return str(args)

print(var_args(1))
#> (1,)
print(var_args(1, 2, 3))
#> (1, 2, 3)

@validate_call
```

---

## r05 (comparison)
**Q:** Why can pip-installed wheels fail in AWS Lambda when built in a local virtual environment?

**Gold passage (pydantic/integrations/aws_lambda#001):**

Pydantic > Aws Lambda > Installing `pydantic` for AWS Lambda functions

When you're building your `.zip` file archive with your code and dependencies or organizing your `.zip` file for a Lambda Layer, you'll likely use a local virtual environment to install and manage your dependencies. This can be a bit tricky if you're using `pip` because `pip` installs wheels compiled for your local platform, which may not be compatible with the Lambda environment.

Thus, we suggest you use a command similar to the following:

```bash
pip install \
    --platform manylinux2014_x86_64 \  # (1)!
    --target=<your_package_dir> \  # (2)!
    --implementation cp \  # (3)!
    --python-version 3.10 \  # (4)!
    --only-binary=:all: \  # (5)!
    --upgrade pydantic  # (6)!
```

1. Use the platform corresponding to your Lambda runtime.
2. Specify the directory where you want to install the package (often `python` for Lambda Layers).
3. Use the CPython implementation.
4. The Python version must be compatible with the Lambda runtime.
5. This flag ensures that the package is installed pre-built binary wheels.
6. The latest version of `pydantic` will be installed.

---

## r06 (factual)
**Q:** Which data sources can datamodel-code-generator turn into Pydantic models?

**Gold passage (pydantic/integrations/datamodel_code_generator#000):**

Pydantic > Code Generation with datamodel-code-generator

The datamodel-code-generator project is a library and command-line utility to generate pydantic models from just about any data source, including:

* OpenAPI 3 (YAML/JSON)
* JSON Schema
* JSON/YAML/CSV Data (which will be converted to JSON Schema)
* Python dictionary (which will be converted to JSON Schema)
* GraphQL schema

Whenever you find yourself with any data convertible JSON but without pydantic models, this tool will allow you to generate type-safe model hierarchies on demand.

---

## r07 (how-to)
**Q:** How do I set the status code inside a path operation function using a temporal Response object?

**Gold passage (fastapi/advanced/response-change-status-code#001):**

FastAPI > Response - Change Status Code > Use a `Response` parameter

You can declare a parameter of type `Response` in your *path operation function* (as you can do for cookies and headers).

And then you can set the `status_code` in that *temporal* response object.

```python
from fastapi import FastAPI, Response, status

app = FastAPI()

tasks = {"foo": "Listen to the Bar Fighters"}

@app.put("/get-or-create-task/{task_id}", status_code=200)
def get_or_create_task(task_id: str, response: Response):
    if task_id not in tasks:
        tasks[task_id] = "This didn't exist before"
        response.status_code = status.HTTP_201_CREATED
    return tasks[task_id]
```

And then you can return any object you need, as you normally would (a `dict`, a database model, etc).

And if you declared a `response_model`, it will still be used to filter and convert the object you returned.

**FastAPI** will use that *temporal* response to extract the status code (also cookies and headers), and will put them in the final response that contains the value you returned, filtered by any `response_model`.

---

## r08 (how-to)
**Q:** How can I validate JSON data from an HTTP API response with a Pydantic model using httpx?

**Gold passage (pydantic/examples/requests#000):**

Pydantic > Requests

Pydantic models are a great way to validating and serializing data for requests and responses.
Pydantic is instrumental in many web frameworks and libraries, such as FastAPI, Django, Flask, and HTTPX.

## `httpx` requests

`httpx` is a HTTP client for Python 3 with synchronous and asynchronous APIs.
In the below example, we query the JSONPlaceholder API to get a user's data and validate it with a Pydantic model.

```python
import httpx

from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

url = 'https://jsonplaceholder.typicode.com/users/1'

response = httpx.get(url)
response.raise_for_status()

user = User.model_validate(response.json())
print(repr(user))
#> User(id=1, name='Leanne Graham', email='Sincere@april.biz')
```

The `TypeAdapter` tool from Pydantic often comes in quite
handy when working with HTTP requests. Consider a similar example where we are validating a list of users:

---

## r09 (factual)
**Q:** What is Pydantic Logfire and what does its Pydantic integration offer?

**Gold passage (pydantic/integrations/logfire#000):**

Pydantic > Logfire

Pydantic integrates seamlessly with **Pydantic Logfire**, an observability platform built by us on the same belief as our open source library — that the most powerful tools can be easy to use.

## Getting Started

Logfire has an out-of-the-box Pydantic integration that lets you understand the data passing through your Pydantic models and get analytics on validations. For existing Pydantic users, it delivers unparalleled insights into your usage of Pydantic models.

Getting started with Logfire can be done in three simple steps:

1. Set up your Logfire account.
2. Install the Logfire SDK.
3. Instrument your project.

### Basic Usage

Once you've got Logfire set up, you can start using it to monitor your Pydantic models and get insights into your data validation:

---

## r10 (how-to)
**Q:** How do I route to an HTTPEndpoint class in a Starlette app without passing an instance?

**Gold passage (starlette/endpoints#001):**

Starlette > Endpoints > HTTPEndpoint

If you're using a Starlette application instance to handle routing, you can
dispatch to an `HTTPEndpoint` class. Make sure to dispatch to the class itself,
rather than to an instance of the class:

```python
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.endpoints import HTTPEndpoint
from starlette.routing import Route

class Homepage(HTTPEndpoint):
    async def get(self, request):
        return PlainTextResponse(f"Hello, world!")

class User(HTTPEndpoint):
    async def get(self, request):
        username = request.path_params['username']
        return PlainTextResponse(f"Hello, {username}")

routes = [
    Route("/", Homepage),
    Route("/{username}", User)
]

app = Starlette(routes=routes)
```

HTTP endpoint classes will respond with "405 Method not allowed" responses for any
request methods which do not map to a corresponding handler.

### WebSocketEndpoint

The `WebSocketEndpoint` class is an ASGI application that presents a wrapper around
the functionality of a `WebSocket` instance.

---

## r11 (comparison)
**Q:** How does validating a Meeting model with strict=True differ from lax mode for the where field?

**Gold passage (pydantic/why#011):**

Pydantic > Why use Pydantic? > Strict mode and data coercion

```python
from datetime import datetime

from pydantic import BaseModel, ValidationError

class Meeting(BaseModel):
    when: datetime
    where: bytes

m = Meeting.model_validate({'when': '2020-01-01T12:00', 'where': 'home'})
print(m)
#> when=datetime.datetime(2020, 1, 1, 12, 0) where=b'home'
try:
    m = Meeting.model_validate(
        {'when': '2020-01-01T12:00', 'where': 'home'}, strict=True
    )
except ValidationError as e:
    print(e)
    """
    2 validation errors for Meeting
    when
      Input should be a valid datetime [type=datetime_type, input_value='2020-01-01T12:00', input_type=str]
    where
      Input should be a valid bytes [type=bytes_type, input_value='home', input_type=str]
    """

m_json = Meeting.model_validate_json(
    '{"when": "2020-01-01T12:00", "where": "home"}'
)
print(m_json)
```

---

## r12 (factual)
**Q:** What is the Starlette application class and what does it tie together?

**Gold passage (starlette/applications#000):**

Starlette > Applications

options:
        parameter_headings: false
        show_root_heading: true
        heading_level: 3
        filters:
            - "__init__"

Starlette includes an application class `Starlette` that nicely ties together all of
its other functionality.

```python
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles

def homepage(request):
    return PlainTextResponse('Hello, world!')

def user_me(request):
    username = "John Doe"
    return PlainTextResponse('Hello, %s!' % username)

def user(request):
    username = request.path_params['username']
    return PlainTextResponse('Hello, %s!' % username)

async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text('Hello, websocket!')
    await websocket.close()

@asynccontextmanager
async def lifespan(app):
    print('Startup')
    yield
    print('Shutdown')

routes = [
```

---

## r13 (how-to)
**Q:** How do I declare a list of dependencies in the decorator that check two custom headers?

**Gold passage (fastapi/tutorial/dependencies/dependencies-in-path-operation-decorators#001):**

FastAPI > Dependencies in path operation decorators > Add `dependencies` to the *path operation decorator*

The *path operation decorator* receives an optional argument `dependencies`.

It should be a `list` of `Depends()`:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

---

## r14 (comparison)
**Q:** How does FastAPI treat frozenset, bytes and Decimal in requests and responses?

**Gold passage (fastapi/tutorial/extra-data-types#002):**

FastAPI > Extra Data Types > Other data types

    * In requests and responses, treated the same as a `set`:

        * In requests, a list will be read, eliminating duplicates and converting it to a `set`.
        * In responses, the `set` will be converted to a `list`.
        * The generated schema will specify that the `set` values are unique (using JSON Schema's `uniqueItems`).
* `bytes`:
    * Standard Python `bytes`.
    * In requests and responses will be treated as `str`.
    * The generated schema will specify that it's a `str` with `binary` "format".
* `Decimal`:
    * Standard Python `Decimal`.
    * In requests and responses, handled the same as a `float`.
* You can check all the valid Pydantic data types here: Pydantic data types.

---

## r15 (factual)
**Q:** Does strict mode with TypeAdapter work for dataclasses and require an instance of the dataclass?

**Gold passage (pydantic/concepts/strict_mode#007):**

Pydantic > Strict Mode > Strict mode in method calls

Note this also works even when using more "complex" types in `TypeAdapter`:

```python
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError

@dataclass
class MyDataclass:
    x: int

try:
    TypeAdapter(MyDataclass).validate_python({'x': '123'}, strict=True)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDataclass
      Input should be an instance of MyDataclass [type=dataclass_exact_type, input_value={'x': '123'}, input_type=dict]
    """
```

This also works with the `TypeAdapter.validate_json` and `BaseModel.model_validate_json` methods:

---

## r16 (how-to)
**Q:** How can I cross-reference Pydantic API docs from my Sphinx project using intersphinx?

**Gold passage (pydantic/integrations/documentation#000):**

Pydantic > Documentation

Pydantic uses MkDocs for documentation, together with
mkdocstrings. As such, you can make use of Pydantic's
Sphinx object inventory to cross-reference the Pydantic API documentation.

In your Sphinx configuration,
add the following to the `intersphinx` extension configuration:

```python
intersphinx_mapping = {
    'pydantic': ('https://docs.pydantic.dev/latest', None),  # (1)!
}
```

1. You can also use `dev` instead of `latest` to target the latest documentation build, up to date
   with the `main` branch.

---

## r17 (comparison)
**Q:** Does the tokenUrl parameter in OAuth2PasswordBearer actually create the token endpoint?

**Gold passage (fastapi/tutorial/security/first-steps#008):**

FastAPI > Security - First Steps > **FastAPI**'s `OAuth2PasswordBearer`

Using a relative URL is important to make sure your application keeps working even in an advanced use case like Behind a Proxy.

This parameter doesn't create that endpoint / *path operation*, but declares that the URL `/token` will be the one that the client should use to get the token. That information is used in OpenAPI, and then in the interactive API documentation systems.

We will soon also create the actual path operation.

If you are a very strict "Pythonista" you might dislike the style of the parameter name `tokenUrl` instead of `token_url`.

That's because it is using the same name as in the OpenAPI spec. So that if you need to investigate more about any of these security schemes you can just copy and paste it to find more information about it.

The `oauth2_scheme` variable is an instance of `OAuth2PasswordBearer`, but it is also a "callable".

It could be called as:

```python
oauth2_scheme(some, parameters)
```

So, it can be used with `Depends`.

### Use it

Now you can pass that `oauth2_scheme` in a dependency with `Depends`.

---

## r18 (factual)
**Q:** How does Starlette generate an OpenAPI schema from application routes and endpoint docstrings?

**Gold passage (starlette/schemas#000):**

Starlette > Schemas

Starlette supports generating API schemas, such as the widely used [OpenAPI
specification][openapi]. (Formerly known as "Swagger".)

Schema generation works by inspecting the routes on the application through
`app.routes`, and using the docstrings or other attributes on the endpoints
in order to determine a complete API schema.

Starlette is not tied to any particular schema generation or validation tooling,
but includes a simple implementation that generates OpenAPI schemas based on
the docstrings.

---

## r19 (how-to)
**Q:** How do I write a ConnectionManager class that keeps active WebSocket connections and broadcasts messages in FastAPI?

**Gold passage (fastapi/advanced/websockets#016):**

FastAPI > WebSockets > Handling disconnections and multiple clients

```python
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
```

---

## r20 (factual)
**Q:** What are Pydantic's dependencies and which Python version does it require?

**Gold passage (pydantic/install#000):**

Pydantic > Install

Installation is as simple as:

```bash
pip install pydantic
```

Pydantic has a few dependencies:

* `pydantic-core`: Core validation logic for Pydantic written in Rust.
* `typing-extensions`: Backport of the standard library typing module.
* `annotated-types`: Reusable constraint types to use with `typing.Annotated`.

If you've got Python 3.9+ and `pip` installed, you're good to go.

Pydantic is also available on conda under the conda-forge
channel:

```bash
conda install pydantic -c conda-forge
```

---

## r21 (factual)
**Q:** In an async FastAPI test, what replaces the synchronous client.get call from TestClient?

**Gold passage (fastapi/advanced/async-tests#005):**

FastAPI > Async Tests > In Detail

Then we can create an `AsyncClient` with the app, and send async requests to it, using `await`.

```python
import pytest
from httpx import ASGITransport, AsyncClient

from .main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}
```

This is the equivalent to:

```python
response = client.get('/')
```

...that we used to make our requests with the `TestClient`.

Note that we're using async/await with the new `AsyncClient` - the request is asynchronous.

If your application relies on lifespan events, the `AsyncClient` won't trigger these events. To ensure they are triggered, use `LifespanManager` from florimondmanca/asgi-lifespan.

---

## r22 (how-to)
**Q:** How do I create and register a custom datetime path convertor in Starlette?

**Gold passage (starlette/routing#002):**

Starlette > Routing > Path Parameters

If you need a different converter that is not defined, you can create your own.
See below an example on how to create a `datetime` convertor, and how to register it:

```python
from datetime import datetime

from starlette.convertors import Convertor, register_url_convertor

class DateTimeConvertor(Convertor):
    regex = "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(.[0-9]+)?"

    def convert(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def to_string(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")

register_url_convertor("datetime", DateTimeConvertor())
```

After registering it, you'll be able to use it as:

```python
Route('/history/{date:datetime}', history)
```

---

## r23 (comparison)
**Q:** Does the order of parameters matter to FastAPI when mixing query and path parameters?

**Gold passage (fastapi/tutorial/path-params-numeric-validations#002):**

FastAPI > Path Parameters and Numeric Validations > Order the parameters as you need

This is probably not as important or necessary if you use `Annotated`.

Let's say that you want to declare the query parameter `q` as a required `str`.

And you don't need to declare anything else for that parameter, so you don't really need to use `Query`.

But you still need to use `Path` for the `item_id` path parameter. And you don't want to use `Annotated` for some reason.

Python will complain if you put a value with a "default" before a value that doesn't have a "default".

But you can re-order them, and have the value without a default (the query parameter `q`) first.

It doesn't matter for **FastAPI**. It will detect the parameters by their names, types and default declarations (`Query`, `Path`, etc), it doesn't care about the order.

So, you can declare your function as:

Prefer to use the `Annotated` version if possible.

---

## r24 (factual)
**Q:** How do include keys with True and nested sets pick fields in model_dump?

**Gold passage (pydantic/concepts/serialization#031):**

Pydantic > Serialization > Advanced include and exclude

```python
    'card_details': True,
    # You can exclude fields from specific members of a tuple/list by index:
    'hobbies': {-1: {'info'}},
}

include_keys = {
    'first_name': True,
    'address': {'country': {'name'}},
    'hobbies': {0: True, -1: {'name'}},
}

# would be the same as user.model_dump(exclude=exclude_keys) in this case:
print(user.model_dump(include=include_keys))
"""
{
    'first_name': 'John',
    'address': {'country': {'name': 'USA'}},
    'hobbies': [
        {'name': 'Programming', 'info': 'Writing code and stuff'},
        {'name': 'Gaming'},
    ],
}
"""

# To exclude a field from all members of a nested list or tuple, use "__all__":
print(user.model_dump(exclude={'hobbies': {'__all__': {'info'}}}))
"""
{
    'first_name': 'John',
    'second_name': 'Doe',
    'address': {
```

---

## r25 (how-to)
**Q:** How do I declare a callback router that posts an InvoiceEvent to the customer-supplied URL in FastAPI?

**Gold passage (fastapi/advanced/openapi-callbacks#003):**

FastAPI > OpenAPI Callbacks > The normal **FastAPI** app

```python
from typing import Union

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI()

class Invoice(BaseModel):
    id: str
    title: Union[str, None] = None
    customer: str
    total: float

class InvoiceEvent(BaseModel):
    description: str
    paid: bool

class InvoiceEventReceived(BaseModel):
    ok: bool

invoices_callback_router = APIRouter()

@invoices_callback_router.post(
    "{$callback_url}/invoices/{$request.body.id}", response_model=InvoiceEventReceived
)
def invoice_notification(body: InvoiceEvent):
    pass

@app.post("/invoices/", callbacks=invoices_callback_router.routes)
def create_invoice(invoice: Invoice, callback_url: Union[HttpUrl, None] = None):
    """
    Create an invoice.

    This will (let's imagine) let the API user (some external developer) create an
    invoice.

    And this path operation will:
```

---

## r26 (comparison)
**Q:** How can I use Starlette as an ASGI toolkit without the full framework?

**Gold passage (starlette/index#004):**

Starlette > Introduction > Framework or Toolkit

Starlette is designed to be used either as a complete framework, or as
an ASGI toolkit. You can use any of its components independently.

```python
from starlette.responses import PlainTextResponse

async def app(scope, receive, send):
    assert scope['type'] == 'http'
    response = PlainTextResponse('Hello, world!')
    await response(scope, receive, send)
```

Run the `app` application in `main.py`:

```shell
$ uvicorn main:app
INFO: Started server process [11509]
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Run uvicorn with `--reload` to enable auto-reloading on code changes.

---

## r27 (factual)
**Q:** Does Pydantic work with mypy without any configuration, and what does the mypy plugin add?

**Gold passage (pydantic/integrations/mypy#000):**

Pydantic > Mypy

Pydantic works well with mypy right out of the box.

However, Pydantic also ships with a mypy plugin that adds a number of important Pydantic-specific
features that improve its ability to type-check your code.

For example, consider the following script:

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: list[int]

m = Model(age=42, list_of_ints=[1, '2', b'3'])
print(m.middle_name)  # not a model field!
Model()  # will raise a validation error for age and list_of_ints
```

Without any special configuration, mypy does not catch the missing model field annotation
and errors about the `list_of_ints` argument which Pydantic parses correctly:

---

## r28 (how-to)
**Q:** How do I use Tag with a callable discriminator to distinguish an int from a model?

**Gold passage (pydantic/concepts/unions#013):**

Pydantic > Unions > Discriminated Unions > Discriminated Unions with callable `Discriminator`

```python
from typing import Annotated, Any, Union

from pydantic import BaseModel, Discriminator, Tag, ValidationError

def model_x_discriminator(v: Any) -> str:
    if isinstance(v, int):
        return 'int'
    if isinstance(v, (dict, BaseModel)):
        return 'model'
    else:
        # return None if the discriminator value isn't found
        return None

class SpecialValue(BaseModel):
    value: int

class DiscriminatedModel(BaseModel):
    value: Annotated[
        Union[
            Annotated[int, Tag('int')],
            Annotated['SpecialValue', Tag('model')],
        ],
        Discriminator(model_x_discriminator),
    ]

model_data = {'value': {'value': 1}}
m = DiscriminatedModel.model_validate(model_data)
print(m)
#> value=SpecialValue(value=1)

int_data = {'value': 123}
m = DiscriminatedModel.model_validate(int_data)
print(m)
#> value=123

try:
    DiscriminatedModel.model_validate({'value': 'not an int or a model'})
```

---

## r29 (comparison)
**Q:** Why must path operation function names be unique if I reuse them as OpenAPI operation IDs?

**Gold passage (fastapi/advanced/path-operation-advanced-configuration#001):**

FastAPI > Path Operation Advanced Configuration > OpenAPI operationId > Using the *path operation function* name as the operationId

You should do it after adding all your *path operations*.

```python
from fastapi import FastAPI
from fastapi.routing import APIRoute

app = FastAPI()

@app.get("/items/")
async def read_items():
    return [{"item_id": "Foo"}]

def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'

use_route_names_as_operation_ids(app)
```

If you manually call `app.openapi()`, you should update the `operationId`s before that.

If you do this, you have to make sure each one of your *path operation functions* has a unique name.

Even if they are in different modules (Python files).

---

## r30 (factual)
**Q:** What does errors() return for a missing field, including loc, msg, input and url?

**Gold passage (pydantic/errors/errors#005):**

Pydantic > Errors

```python
                'a_float': 3.0,
                'recursive_model': {'lat': 4.2, 'lng': 'New York'},
                'gt_int': 21,
            },
            'url': 'https://errors.pydantic.dev/2/v/missing',
        },
        {
            'type': 'greater_than',
            'loc': ('gt_int',),
            'msg': 'Input should be greater than 42',
            'input': 21,
            'ctx': {'gt': 42},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        },
        {
            'type': 'int_parsing',
            'loc': ('list_of_ints', 2),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'bad',
            'url': 'https://errors.pydantic.dev/2/v/int_parsing',
        },
        {
            'type': 'value_error',
            'loc': ('a_float',),
```

---

## r31 (how-to)
**Q:** Why should only requirements.txt be copied into the image before the rest of the code in a FastAPI Dockerfile?

**Gold passage (fastapi/deployment/docker#008):**

FastAPI > FastAPI in Containers - Docker > Build a Docker Image for FastAPI > Dockerfile

Now in the same project directory create a file `Dockerfile` with:

```
# (1)!
FROM python:3.9

# (2)!
WORKDIR /code

# (3)!
COPY ./requirements.txt /code/requirements.txt

# (4)!
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# (5)!
COPY ./app /code/app

# (6)!
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

1. Start from the official Python base image.

2. Set the current working directory to `/code`.

    This is where we'll put the `requirements.txt` file and the `app` directory.

3. Copy the file with the requirements to the `/code` directory.

    Copy **only** the file with the requirements first, not the rest of the code.

    As this file **doesn't change often**, Docker will detect it and use the **cache** for this step, enabling the cache for the next step too.

4. Install the package dependencies in the requirements file.

---

## r32 (comparison)
**Q:** Why can't I declare both Form fields and JSON Body fields in the same path operation?

**Gold passage (fastapi/tutorial/request-forms#003):**

FastAPI > Form Data > About "Form Fields"

The way HTML forms (``) sends the data to the server normally uses a "special" encoding for that data, it's different from JSON.

**FastAPI** will make sure to read that data from the right place instead of JSON.

Data from forms is normally encoded using the "media type" `application/x-www-form-urlencoded`.

But when the form includes files, it is encoded as `multipart/form-data`. You'll read about handling files in the next chapter.

If you want to read more about these encodings and form fields, head to the MDN web docs for POST.

You can declare multiple `Form` parameters in a *path operation*, but you can't also declare `Body` fields that you expect to receive as JSON, as the request will have the body encoded using `application/x-www-form-urlencoded` instead of `application/json`.

This is not a limitation of **FastAPI**, it's part of the HTTP protocol.

## Recap

Use `Form` to declare form data input parameters.

---

## r33 (factual)
**Q:** Which decorator parameter omits values that were not actually set when returning a model?

**Gold passage (fastapi/tutorial/response-model#019):**

FastAPI > Response Model - Return Type > Response Model encoding parameters

* `description: Union[str, None] = None` (or `str | None = None` in Python 3.10) has a default of `None`.
* `tax: float = 10.5` has a default of `10.5`.
* `tags: List[str] = []` has a default of an empty list: `[]`.

but you might want to omit them from the result if they were not actually stored.

For example, if you have models with many optional attributes in a NoSQL database, but you don't want to send very long JSON responses full of default values.

### Use the `response_model_exclude_unset` parameter

You can set the *path operation decorator* parameter `response_model_exclude_unset=True`:

---

## r34 (how-to)
**Q:** How do I serve static files from a directory in FastAPI with StaticFiles?

**Gold passage (fastapi/tutorial/static-files#000):**

FastAPI > Static Files

You can serve static files automatically from a directory using `StaticFiles`.

## Use `StaticFiles`

* Import `StaticFiles`.
* "Mount" a `StaticFiles()` instance in a specific path.

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
```

You could also use `from starlette.staticfiles import StaticFiles`.

**FastAPI** provides the same `starlette.staticfiles` as `fastapi.staticfiles` just as a convenience for you, the developer. But it actually comes directly from Starlette.

### What is "Mounting"

"Mounting" means adding a complete "independent" application in a specific path, that then takes care of handling all the sub-paths.

This is different from using an `APIRouter` as a mounted application is completely independent. The OpenAPI and docs from your main application won't include anything from the mounted application, etc.

You can read more about this in the Advanced User Guide.

---

## r35 (comparison)
**Q:** Is giving root_path to the FastAPI constructor equivalent to the --root-path option of Uvicorn?

**Gold passage (fastapi/advanced/behind-a-proxy#005):**

FastAPI > Behind a Proxy > Proxy with a stripped path prefix > Checking the current `root_path`

The response would be something like:

```json
{
    "message": "Hello World",
    "root_path": "/api/v1"
}
```

### Setting the `root_path` in the FastAPI app

Alternatively, if you don't have a way to provide a command line option like `--root-path` or equivalent, you can set the `root_path` parameter when creating your FastAPI app:

```python
from fastapi import FastAPI, Request

app = FastAPI(root_path="/api/v1")

@app.get("/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": request.scope.get("root_path")}
```

Passing the `root_path` to `FastAPI` would be the equivalent of passing the `--root-path` command line option to Uvicorn or Hypercorn.

### About `root_path`

Keep in mind that the server (Uvicorn) won't use that `root_path` for anything else than passing it to the app.

But if you go with your browser to http://127.0.0.1:8000/app you will see the normal response:

---

## r36 (factual)
**Q:** In the concurrent burgers story, what does the person do while waiting for the order after paying?

**Gold passage (fastapi/async#006):**

FastAPI > Concurrency and async / await > Asynchronous Code > Concurrent Burgers

You pay. 💸

The cashier gives you the number of your turn.

While you are waiting, you go with your crush and pick a table, you sit and talk with your crush for a long time (as your burgers are very fancy and take some time to prepare).

As you are sitting at the table with your crush, while you wait for the burgers, you can spend that time admiring how awesome, cute and smart your crush is ✨😍✨.

While waiting and talking to your crush, from time to time, you check the number displayed on the counter to see if it's your turn already.

Then at some point, it finally is your turn. You go to the counter, get your burgers and come back to the table.

You and your crush eat the burgers and have a nice time. ✨

Beautiful illustrations by Ketrina Thompson. 🎨

---

Imagine you are the computer / program 🤖 in that story.

While you are at the line, you are just idle 😴, waiting for your turn, not doing anything very "productive". But the line is fast because the cashier is only taking the orders (not preparing them), so that's fine.

---

## r37 (comparison)
**Q:** Who normally handles HTTPS for a FastAPI container, and how can Traefik help?

**Gold passage (fastapi/deployment/docker#020):**

FastAPI > FastAPI in Containers - Docker > HTTPS

If we focus just on the **container image** for a FastAPI application (and later the running **container**), HTTPS normally would be handled **externally** by another tool.

It could be another container, for example with Traefik, handling **HTTPS** and **automatic** acquisition of **certificates**.

Traefik has integrations with Docker, Kubernetes, and others, so it's very easy to set up and configure HTTPS for your containers with it.

Alternatively, HTTPS could be handled by a cloud provider as one of their services (while still running the application in a container).

---

## r38 (how-to)
**Q:** How do I use PlainSerializer to format an integer as a string with thousands separators only in JSON mode?

**Gold passage (pydantic/concepts/serialization#011):**

Pydantic > Serialization > Custom serializers

`PlainSerializer` uses a simple function to modify the output of serialization.

```python
from typing import Annotated

from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

FancyInt = Annotated[
    int, PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json')
]

class MyModel(BaseModel):
    x: FancyInt

print(MyModel(x=1234).model_dump())
#> {'x': 1234}

print(MyModel(x=1234).model_dump(mode='json'))
#> {'x': '1,234'}
```

`WrapSerializer` receives the raw inputs along with a handler function that applies the standard serialization
logic, and can modify the resulting value before returning it as the final output of serialization.

---

## r39 (how-to)
**Q:** How do I keep a union return type annotation like Response or dict without FastAPI trying to build a response model?

**Gold passage (fastapi/tutorial/response-model#017):**

FastAPI > Response Model - Return Type > Other Return Type Annotations > Invalid Return Type Annotations

...this fails because the type annotation is not a Pydantic type and is not just a single `Response` class or subclass, it's a union (any of the two) between a `Response` and a `dict`.

### Disable Response Model

Continuing from the example above, you might not want to have the default data validation, documentation, filtering, etc. that is performed by FastAPI.

But you might want to still keep the return type annotation in the function to get the support from tools like editors and type checkers (e.g. mypy).

In this case, you can disable the response model generation by setting `response_model=None`:

```python
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/portal", response_model=None)
async def get_portal(teleport: bool = False) -> Response | dict:
    if teleport:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    return {"message": "Here's your interdimensional portal."}
```

---

## r40 (comparison)
**Q:** Why does Uvicorn not expect requests at /api/v1/app even though the root path is set to /api/v1?

**Gold passage (fastapi/advanced/behind-a-proxy#006):**

FastAPI > Behind a Proxy > Proxy with a stripped path prefix > About `root_path`

But if you go with your browser to http://127.0.0.1:8000/app you will see the normal response:

```json
{
    "message": "Hello World",
    "root_path": "/api/v1"
}
```

So, it won't expect to be accessed at `http://127.0.0.1:8000/api/v1/app`.

Uvicorn will expect the proxy to access Uvicorn at `http://127.0.0.1:8000/app`, and then it would be the proxy's responsibility to add the extra `/api/v1` prefix on top.

---

## r41 (comparison)
**Q:** What happens when a path operation function is declared with plain def instead of async def?

**Gold passage (fastapi/async#022):**

FastAPI > Concurrency and async / await > Very Technical Details

You can probably skip this.

These are very technical details of how **FastAPI** works underneath.

If you have quite some technical knowledge (coroutines, threads, blocking, etc.) and are curious about how FastAPI handles `async def` vs normal `def`, go ahead.

### Path operation functions

When you declare a *path operation function* with normal `def` instead of `async def`, it is run in an external threadpool that is then awaited, instead of being called directly (as it would block the server).

If you are coming from another async framework that does not work in the way described above and you are used to defining trivial compute-only *path operation functions* with plain `def` for a tiny performance gain (about 100 nanoseconds), please note that in **FastAPI** the effect would be quite opposite. In these cases, it's better to use `async def` unless your *path operation functions* use code that performs blocking I/O.

Still, in both situations, chances are that **FastAPI** will still be faster than (or at least comparable to) your previous framework.

---

## r42 (factual)
**Q:** How do union validation errors name each branch when members are annotated with a Tag?

**Gold passage (pydantic/concepts/unions#025):**

Pydantic > Unions > Union Validation Errors

```python
        Annotated[DoubledList, Tag('DoubledList')],
        Annotated[StringsMap, Tag('StringsMap')],
    ]
)

try:
    tag_adapter.validate_python(['a'])
except ValidationError as exc_info:
    print(exc_info)
    """
    2 validation errors for union[DoubledList,StringsMap]
    DoubledList.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    StringsMap
      Input should be a valid dictionary [type=dict_type, input_value=['a'], input_type=list]
    """
```

---

## r43 (factual)
**Q:** Which extra dependency do I need to use ORJSONResponse in FastAPI?

**Gold passage (fastapi/index#019):**

FastAPI > FastAPI > Dependencies > Additional Optional Dependencies

There are some additional dependencies you might want to install.

Additional optional Pydantic dependencies:

* pydantic-settings - for settings management.
* pydantic-extra-types - for extra types to be used with Pydantic.

Additional optional FastAPI dependencies:

* orjson - Required if you want to use `ORJSONResponse`.
* ujson - Required if you want to use `UJSONResponse`.

## License

This project is licensed under the terms of the MIT license.

---

## r44 (how-to)
**Q:** How can I stop FastAPI from showing the entire docstring of a path operation in the OpenAPI description?

**Gold passage (fastapi/advanced/path-operation-advanced-configuration#003):**

FastAPI > Path Operation Advanced Configuration > Advanced description from docstring

You can limit the lines used from the docstring of a *path operation function* for OpenAPI.

Adding an `\f` (an escaped "form feed" character) causes **FastAPI** to truncate the output used for OpenAPI at this point.

It won't show up in the documentation, but other tools (such as Sphinx) will be able to use the rest.

---

## r45 (factual)
**Q:** Where can I check which input types are accepted in strict mode?

**Gold passage (pydantic/concepts/strict_mode#005):**

Pydantic > Strict Mode > Type coercions in strict mode

```python
            'input': '12345678-1234-1234-1234-123456789012',
            'ctx': {'class': 'UUID'},
        }
    ]
    """
```

For more details about what types are allowed as inputs in strict mode, you can review the
Conversion Table.

---

## r46 (factual)
**Q:** Do multiple messages in the chat example share a single WebSocket connection?

**Gold passage (fastapi/advanced/websockets#008):**

FastAPI > WebSockets > Try it

If your file is named `main.py`, run your application with:

```console
$ fastapi dev main.py

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Open your browser at http://127.0.0.1:8000.

You will see a simple page like:

You can type messages in the input box, and send them:

And your **FastAPI** application with WebSockets will respond back:

You can send (and receive) many messages:

And all of them will use the same WebSocket connection.

---

## r47 (factual)
**Q:** What timing does Pydantic's validate_json reach on the emoji data benchmark compared to pure Python?

**Gold passage (pydantic/why#005):**

Pydantic > Why use Pydantic? > Performance

```python
type_adapter = TypeAdapter(dict[str, HttpUrl])
emojis_pydantic_times = timeit.repeat(
    'type_adapter.validate_json(emojis_json)',
    globals={
        'type_adapter': type_adapter,
        'HttpUrl': HttpUrl,
        'emojis_json': emojis_json,
    },
    repeat=reps,
    number=number,
)
print(f'pydantic: {min(emojis_pydantic_times) / number * 1000:0.2f}ms')
#> pydantic: 1.54ms

print(
    f'Pydantic {min(emojis_pure_python_times) / min(emojis_pydantic_times):0.2f}x faster'
)
#> Pydantic 3.45x faster
```

Unlike other performance-centric libraries written in compiled languages, Pydantic also has excellent support for customizing validation via functional validators.

Samuel Colvin's talk at PyCon 2023 explains how `pydantic-core`
works and how it integrates with Pydantic.

---

## r48 (how-to)
**Q:** How do I use an alias together with a gt constraint on a validated function argument?

**Gold passage (pydantic/concepts/validation_decorator#008):**

Pydantic > Validation Decorator > Using the `Field()` function to describe function parameters

Aliases can be used with the decorator as normal:

```python
from typing import Annotated

from pydantic import Field, validate_call

@validate_call
def how_many(num: Annotated[int, Field(gt=10, alias='number')]):
    return num

how_many(number=42)
```

---

## r49 (how-to)
**Q:** How can I generate a URL for a named route with request.url_for in Starlette?

**Gold passage (starlette/routing#006):**

Starlette > Routing > Reverse URL lookups

You'll often want to be able to generate the URL for a particular route,
such as in cases where you need to return a redirect response.

* Signature: `url_for(name, **path_params) -> URL`

```python
routes = [
    Route("/", homepage, name="homepage")
]

# We can use the following to return a URL...
url = request.url_for("homepage")
```

URL lookups can include path parameters...

```python
routes = [
    Route("/users/{username}", user, name="user_detail")
]

# We can use the following to return a URL...
url = request.url_for("user_detail", username=...)
```

If a `Mount` includes a `name`, then submounts should use a `{prefix}:{name}`
style for reverse URL lookups.

---

