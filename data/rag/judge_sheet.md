# RAG judging sheet (blinded)

## r00 (factual)
**Question:** Can I set headers and cookies through a Response parameter inside a dependency?

**Reference:** Yes. A Response parameter can also be declared in dependencies, where you can set headers and cookies on it just as in a path operation function; FastAPI extracts them from that temporary response.

**Answer X:** Yes, you can set headers and cookies through a Response parameter inside a dependency.

**Answer Y:** Yes, you can set headers and cookies through a Response parameter inside a dependency.

---

## r01 (how-to)
**Question:** How do I validate a list of TypedDict users with a TypeAdapter?

**Reference:** Create a TypeAdapter for list[User], where User is a TypedDict, and call validate_python on the list of dicts. Values are coerced (id '3' becomes 3) and invalid items raise a ValidationError naming the index and field, like 0.id.

**Answer X:** To validate a list of TypedDict users with a TypeAdapter, you can use the `TypeAdapter` class and provide a `config` argument. Here's how you can do it:

```python
from typing import Annotated, TypeVar

from annotated_types import Gt, Len

from pydantic import TypeAdapter, ValidationError

T = TypeVar('T')

ShortList = Annotated[list[T], Len(max_length=4)]

ta = TypeAdapter(ShortList[int])

v = ta.validate_python([1, 2, 3, 4])
assert v == [1, 2, 3, 4]

try:
    ta.validate_python([1, 2, 3, 4, 5])
except ValidationError as exc:
    print(exc)
    """
    1 validation error for list[int]
      List should have at most 4 items after validation, not 5 [type=too_long, input_value=[1, 2

**Answer Y:** To validate a list of `TypedDict` users with a `TypeAdapter`, you can use the `validate_python` method. Here's how you can do it:

```python
from typing_extensions import TypedDict
from pydantic import TypeAdapter, ValidationError

class User(TypedDict):
    name: str
    id: int

user_list_adapter = TypeAdapter(list[User])
user_list = user_list_adapter.validate_python([{'name': 'Fred', 'id': '3'}])
print(repr(user_list))  # Output: [{'name': 'Fred', 'id': 3}]
```

In this example, we create a `User` typed dictionary and then use `validate_python` to validate a Python list containing such a typed dictionary. The result is a validated list of `User` objects.

---

## r02 (comparison)
**Question:** Why does the tutorial strongly encourage running and editing the examples in my own editor?

**Reference:** Because writing or copying the code, editing it and running it locally in your editor shows the real benefits of FastAPI: how little code you write, the type checks and the autocompletion.

**Answer X:** The tutorial strongly encourages running and editing the examples in your own editor because it provides hands-on experience with the core concepts and functionalities of FastAPI, allowing you to understand how to integrate it into your existing development workflow effectively. This practical approach helps reinforce learning and ensures that you are comfortable working within the framework's constraints and limitations.

**Answer Y:** To run and edit the examples in your own editor, simply activate the virtual environment and then run your program.

---

## r03 (factual)
**Question:** Which large companies are quoted as using FastAPI for ML services or open source frameworks?

**Reference:** Microsoft (ML services, some integrated into Windows and Office), Uber (a REST server for predictions for Ludwig) and Netflix (the open-source crisis management framework Dispatch, built with FastAPI).

**Answer X:** Microsoft, Netflix, Uber, Lyft, SpaceX, IBM, Google, Amazon, Microsoft Azure, AWS, Facebook, Twitter, Alibaba, Tencent, Oracle, SAP, Salesforce, Cisco, HP, Dell, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo, HP, Lenovo

**Answer Y:** Microsoft, Uber, Netflix

---

## r04 (how-to)
**Question:** How do I declare positional-only and keyword-only parameters in a function decorated with validate_call?

**Reference:** Use the validate_call decorator. Keyword-only parameters come after a bare * (def f(*, a, b=2)); positional-only parameters come before a / (def f(a, b=2, /)); *args and **kwargs are supported too.

**Answer X:** To declare positional-only and keyword-only parameters in a function decorated with `validate_call`, use the following syntax:

- **Positional-only arguments**: Use `*` to indicate that they are optional.
- **Keyword-only arguments**: Use `**` to indicate that they are required.

Example:

```python
from pydantic import validate_call

@validate_call
def foo(a: int, b: str = None) -> int:
    return a + b

# Example usage:
print(foo(1))  # Output: 1
print(foo(1, "hello"))  # Raises ValueError: missing_positional_only_argument
```

**Answer Y:** To declare positional-only and keyword-only parameters in a function decorated with `validate_call`, use the following syntax:

```python
@validate_call
def foo(a: int, b: str) -> None:
    pass
```

In this example, `a` is declared as positional-only and `b` as keyword-only.

---

## r05 (comparison)
**Question:** Why can pip-installed wheels fail in AWS Lambda when built in a local virtual environment?

**Reference:** pip installs wheels compiled for your local platform, which may not be compatible with the Lambda environment. Install with --platform (e.g. manylinux2014_x86_64), --python-version, --implementation cp and --only-binary=:all: matching the Lambda runtime.

**Answer X:** Pip-installed wheels are typically incompatible with AWS Lambda due to their platform-specific nature. To resolve this issue, you should upgrade pip before installing packages.

**Answer Y:** Pip-installed wheels for AWS Lambda are not compatible with the specific versions of Python and Lambda environments used. These issues arise due to differences between pip and the actual Python interpreter running on the Lambda instance.

---

## r06 (factual)
**Question:** Which data sources can datamodel-code-generator turn into Pydantic models?

**Reference:** OpenAPI 3 (YAML/JSON), JSON Schema, JSON/YAML/CSV data and Python dictionaries (converted to JSON Schema) and GraphQL schemas.

**Answer X:** OpenAPI 3 (YAML/JSON), JSON Schema, JSON/YAML/CSV Data

**Answer Y:** OpenAPI 3 (YAML/JSON), JSON Schema, JSON/YAML/CSV Data, Python dictionary

---

## r07 (how-to)
**Question:** How do I set the status code inside a path operation function using a temporal Response object?

**Reference:** Declare a parameter of type Response in the path operation function and set response.status_code on it, e.g. status.HTTP_201_CREATED. FastAPI takes the status code from that temporary response, and response_model still filters the returned data.

**Answer X:** To set the status code inside a path operation function using a temporal Response object, you can follow these steps:

1. Declare a parameter of type `Response` in your path operation function.
2. Set the `status_code` in that `temporal` response object.

Example:

```python
from fastapi import FastAPI, Response, status

app = FastAPI()

@app.put("/get-or-create-task/{task_id}", status_code=200)
def get_or_create_task(task_id: str, response: Response):
    if task_id not in tasks:
        tasks[task_id] = "This didn't exist before"
        response.status_code = status.HTTP_201_CREATED
    return tasks[task_id]

# Example usage
import datetime

now = datetime.datetime.now()
print(f"Task {task_id} created on {now}")
```

In this example, when creating a new task, the status code is set to 201 Created,

**Answer Y:** To set the status code inside a path operation function using a temporal Response object, you can follow these steps:

1. Declare a parameter of type `Response` in your path operation function.
2. Set the `status_code` in that `temporal` response object.

Example:

```python
from fastapi import FastAPI, Response, status

app = FastAPI()

@app.put("/get-or-create-task/{task_id}", status_code=200)
def get_or_create_task(task_id: str, response: Response):
    if task_id not in tasks:
        tasks[task_id] = "This didn't exist before"
        response.status_code = status.HTTP_201_CREATED
    return tasks[task_id]
```

In this example, the `status_code` is set to `201 Created` when the task is created.

---

## r08 (how-to)
**Question:** How can I validate JSON data from an HTTP API response with a Pydantic model using httpx?

**Reference:** Call httpx.get(url), raise_for_status(), then pass response.json() to User.model_validate() on a BaseModel such as User(id, name, email). For a list of users use a TypeAdapter.

**Answer X:** To validate JSON data from an HTTP API response with a Pydantic model using httpx, you can use the `model_validate_json()` method. This method parses the JSON string or bytes object as a JSON mode object and validates the data accordingly.

**Answer Y:** To validate JSON data from an HTTP API response with a Pydantic model using `httpx`, you can follow these steps:

1. **Query the JSON Placeholder API**: Use `httpx` to make a GET request to the specified endpoint.
2. **Parse the JSON Response**: Extract the JSON data from the response.
3. **Validate the Model**: Create a Pydantic model instance and validate the extracted JSON data against the model schema.

Here’s a step-by-step example:

```python
import httpx
from pydantic import BaseModel, EmailStr, ValidationError
from fastapi.testclient import TestClient
from unittest.mock import patch

# Define the Pydantic model
class User(BaseModel):
    id: int
    name: str
    email: EmailStr

# Example JSON data from the API
json_data = {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
}

---

## r09 (factual)
**Question:** What is Pydantic Logfire and what does its Pydantic integration offer?

**Reference:** Logfire is an observability platform from the Pydantic team. Its Pydantic integration shows the data passing through your models and gives analytics on validations. You set up an account, install the SDK and instrument your project.

**Answer X:** Pydantic Logfire is an observability platform built by the same team as Pydantic, providing seamless integration between Pydantic models and Logfire's application monitoring capabilities. It offers unparalleled insights into Pydantic model usage and data validation, making it easier to understand and improve Pydantic models.

**Answer Y:** Pydantic Logfire is an observability platform built by the same team as Pydantic, providing seamless integration between Pydantic models and Logfire's application monitoring capabilities. It offers unparalleled insights into Pydantic model usage and validation, making it easier to understand data flow and identify issues.

---

## r10 (how-to)
**Question:** How do I route to an HTTPEndpoint class in a Starlette app without passing an instance?

**Reference:** Pass the HTTPEndpoint class itself, not an instance, to a Route, e.g. Route('/', Homepage), in the routes list of the Starlette app. Methods the class does not implement return 405 Method Not Allowed.

**Answer X:** To route to an `HTTPEndpoint` class in a Starlette app without passing an instance, you dispatch directly to the class itself rather than to an instance of it. For example, if you want to route to the `Homepage` class, you would use:

```python
@app.get("/")
def home():
    return PlainTextResponse("Hello, world!")
```

This way, the `HomePage` class is dispatched to the `get` method, and the `PlainTextResponse` is returned.

**Answer Y:** To route to an `HTTPEndpoint` class in a Starlette app without passing an instance, use the `@route` decorator directly on the class definition. This allows you to specify the URL path directly within the class definition. For example:

```python
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

class MyApp(HTTPEndpoint):
    @route("/")
    async def get(self, request):
        return PlainTextResponse("Hello, world!")

routes = [
    Route("/", MyApp),
]
app = Starlette(routes=routes)
```

This approach ensures that your `MyApp` class is correctly dispatched to the `get` endpoint without needing to pass an instance.

---

## r11 (comparison)
**Question:** How does validating a Meeting model with strict=True differ from lax mode for the where field?

**Reference:** In lax mode '2020-01-01T12:00' is parsed into a datetime and 'home' into bytes. With strict=True both fields fail, since Python str input is not a datetime or bytes instance (validating from JSON still works).

**Answer X:** Validating a Meeting model with strict=True differs from lax mode for the where field because it ensures that the date format is strictly adhered to, preventing invalid dates.

**Answer Y:** The where field is validated strictly, whereas the lax mode allows for more flexibility but may lead to errors due to coercion issues.

---

## r12 (factual)
**Question:** What is the Starlette application class and what does it tie together?

**Reference:** The Starlette class ties together all the other functionality: routes (Route, Mount, WebSocketRoute), static files, lifespan and so on, configured in a single application object.

**Answer X:** The Starlette application class ties together all of its other functionality.

**Answer Y:** The Starlette application class allows you to include the ASGI middleware in a way that ensures it remains wrapped by the exception handler. It wraps all Starlette routes, providing a centralized point for handling incoming requests and routing them through the middleware stack.

---

## r13 (how-to)
**Question:** How do I declare a list of dependencies in the decorator that check two custom headers?

**Reference:** Pass dependencies=[Depends(verify_token), Depends(verify_key)] to the path operation decorator. Each dependency reads a header (X-Token, X-Key) with Header() and raises an HTTPException if it is invalid.

**Answer X:** To declare a list of dependencies for checking two custom headers, you can use the following format within the `dependencies` attribute of a decorated function:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

@app.get("/items/")
async def read_items(x_token: Annotated[list[str] | None, Header()], x_key: Annotated[str | None, Header()]):
    if x_token is None or x_key is None:
        raise HTTPException(status_code=400, detail="Missing required headers")
    
    # Process the headers here
    return {"X-Token values": x_token, "X-Key values": x_key}
```

In this example, the `dependencies` attribute is defined as a list containing two `Depends` objects, one for each custom header. The first depends on the `x_token` header, and the second depends on the `x_key` header.

**Answer Y:** To declare a list of dependencies in the decorator that checks two custom headers, you can use the following syntax:

```python
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: Annotated[str, Header()], y_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token" and y_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="Invalid token combination")

async def verify_key(x_key: Annotated[str, Header()], y_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key" and y_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="Invalid key combination")

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo

---

## r14 (comparison)
**Question:** How does FastAPI treat frozenset, bytes and Decimal in requests and responses?

**Reference:** frozenset is treated like a set (a list in requests is deduplicated into a set; responses convert it to a list; the schema marks uniqueItems). bytes is treated as str with binary format in the schema. Decimal is handled like a float.

**Answer X:** In requests and responses, a frozenset will be treated as a set, converted to a list, and specified as a `set` in the generated schema.

**Answer Y:** In requests, a frozen set is treated as a set, and in responses, it is converted to a list. The generated schema specifies that the set values are unique using JSON Schema's `uniqueItems`.

---

## r15 (factual)
**Question:** Does strict mode with TypeAdapter work for dataclasses and require an instance of the dataclass?

**Reference:** Yes. strict mode works with TypeAdapter for dataclasses. Passing a plain dict with strict=True fails with 'Input should be an instance of MyDataclass'.

**Answer X:** Yes, strict mode with TypeAdapter works for dataclasses and requires an instance of the dataclass.

**Answer Y:** Yes, strict mode with TypeAdapter works for dataclasses and requires an instance of the dataclass.

---

## r16 (how-to)
**Question:** How can I cross-reference Pydantic API docs from my Sphinx project using intersphinx?

**Reference:** Add intersphinx_mapping = {'pydantic': ('https://docs.pydantic.dev/latest', None)} to your Sphinx configuration (use dev instead of latest for the latest main build).

**Answer X:** To cross-reference Pydantic API docs from your Sphinx project, you can add the following to your Sphinx configuration:

```python
intersphinx_mapping = {
    'pydantic': ('https://docs.pydantic.dev/latest', None),
}
```

This will allow you to access the Pydantic API documentation within your Sphinx documentation.

**Answer Y:** You can use the `intersphinx_mapping` setting in your Sphinx configuration to reference Pydantic API documentation. For example:

```python
intersphinx_mapping = {
    'pydantic': ('https://docs.pydantic.dev/latest', None),
}
```

This will automatically include Pydantic documentation when generating Sphinx HTML pages.

---

## r17 (comparison)
**Question:** Does the tokenUrl parameter in OAuth2PasswordBearer actually create the token endpoint?

**Reference:** No. tokenUrl only declares which URL the client should use to get the token, which is used by OpenAPI and the interactive docs. You still have to create the actual path operation.

**Answer X:** Yes, the tokenUrl parameter in OAuth2PasswordBearer creates the token endpoint. It specifies the URL where the client (frontend) will send username and password to obtain a token.

**Answer Y:** Yes, the tokenUrl parameter in OAuth2PasswordBearer creates the token endpoint.

---

## r18 (factual)
**Question:** How does Starlette generate an OpenAPI schema from application routes and endpoint docstrings?

**Reference:** Schema generation inspects app.routes and uses the docstrings or other attributes of the endpoints to build the schema. Starlette includes a simple implementation that generates OpenAPI from docstrings, but it is not tied to any particular tooling.

**Answer X:** Starlette generates an OpenAPI schema from application routes and endpoint docstrings by inspecting the routes on the application through `app.routes` and using the docstrings or other attributes on the endpoints to determine a complete API schema.

**Answer Y:** Starlette uses the `app.routes` attribute to identify routes and their corresponding endpoints, then applies the `docstrings` or other attributes to infer the complete API schema. This allows it to dynamically generate OpenAPI schemas without relying on specific tools or frameworks.

---

## r19 (how-to)
**Question:** How do I write a ConnectionManager class that keeps active WebSocket connections and broadcasts messages in FastAPI?

**Reference:** Write a class with an active_connections list, an async connect that accepts and appends the websocket, a disconnect that removes it, send_personal_message, and a broadcast method that loops over all connections sending the text.

**Answer X:** ```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Initialize the ConnectionManager
connection_manager = ConnectionManager()

# Define the WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(ws: WebSocket, client_id: int):
    await connection_manager.connect(ws)
    
    try:
        while True:
            data = await ws.recv_text()
            await connection_manager.send_personal_message(f"You wrote: {data}", ws)
            await connection_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(ws)
        await connection_manager.broadcast(f"Client #{client_id} left the chat")

# Function to broadcast messages
def broadcast_messages(client_id: int, messages: list[str]):
    for connection in connection_manager.active_connections:
        await connection.send_text(f"Client #{client_id} says: {messages}")

#

**Answer Y:** ```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Initialize the ConnectionManager
connection_manager = ConnectionManager()

# Define the WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.send_personal_message(f"You wrote: {data}", websocket)
            await connection_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        await connection_manager.broadcast(f"Client #{client_id} left the chat")

# Function to broadcast messages
def broadcast_messages(websocket: WebSocket):
    while True:
        try:
            message = await websocket.receive_text()
            await connection_manager.broadcast(f"Client #{websocket.client_id} says

---

## r20 (factual)
**Question:** What are Pydantic's dependencies and which Python version does it require?

**Reference:** pydantic-core (the Rust validation core), typing-extensions and annotated-types. Python 3.9+ with pip is enough.

**Answer X:** Pydantic has several dependencies:

* `pydantic-core`: Core validation logic in Rust.
* `typing-extensions`: Backported standard library typing module.
* `annotated-types`: Reusable constraint types for `typing.Annotated`.

For Python 3.9+, Pydantic is available on conda under the conda-forge channel:

```bash
conda install pydantic -c conda-forge
```

The required Python version for Pydantic is 3.9+.

**Answer Y:** Pydantic has several dependencies:

* `pydantic-core`: Core validation logic for Pydantic written in Rust.
* `typing-extensions`: Backport of the standard library typing module.
* `annotated-types`: Reusable constraint types to use with `typing.Annotated`.

It requires Python 3.9+ and `pip` installed.

---

## r21 (factual)
**Question:** In an async FastAPI test, what replaces the synchronous client.get call from TestClient?

**Reference:** An httpx AsyncClient created with ASGITransport(app=app) and a base_url, used as await ac.get('/') inside an async test marked with @pytest.mark.anyio.

**Answer X:** In an async FastAPI test, the replacement for the synchronous client.get call from TestClient is using the `AsyncClient` directly, which sends async requests to the FastAPI application.

**Answer Y:** In an async FastAPI test, the replacement for the synchronous client.get call from TestClient is using the `AsyncClient` directly, which sends async requests to the FastAPI application.

---

## r22 (how-to)
**Question:** How do I create and register a custom datetime path convertor in Starlette?

**Reference:** Subclass Convertor with a regex, convert() and to_string() methods, register it with register_url_convertor('datetime', DateTimeConvertor()), then use it in paths such as '/history/{date:datetime}'.

**Answer X:** To create and register a custom datetime path convertor in Starlette, follow these steps:

1. **Create the Custom Convertor Class**: Define a new class that inherits from `Convertor`.
2. **Define the Regex Pattern**: Implement the `regex` attribute to define the pattern for parsing dates.
3. **Implement the Convert Method**: Override the `convert` method to parse the date string according to the defined pattern.
4. **Register the Convertor**: Use the `register_url_convertor` function to register the custom convertor with the URL router.

Here’s an example implementation:

```python
import re
from starlette.convertors import Convertor, register_url_convertor

class DateTimeConvertor(Convertor):
    regex = r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+'

    async def convert(self, value: str) -> datetime:

**Answer Y:** To create and register a custom datetime path convertor in Starlette, follow these steps:

1. **Define the Convertor Class**: Create a class named `DateTimeConvertor` that inherits from `Convertor`. This class should have methods for converting between `datetime` objects and strings.

   ```python
   from datetime import datetime

   from starlette.convertors import Convertor, register_url_convertor

   class DateTimeConvertor(Convertor):
       regex = "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(.[0-9]+)?"

       def convert(self, value: str) -> datetime:
           return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

       def to_string(self, value: datetime) -> str:
           return value.strftime("%Y-%m-%dT%H:%M

---

## r23 (comparison)
**Question:** Does the order of parameters matter to FastAPI when mixing query and path parameters?

**Reference:** No. FastAPI detects parameters by name, type and default declarations (Query, Path), not by order, so the required query parameter q can come first (or you can use * as the first parameter). Annotated avoids the problem.

**Answer X:** Yes, the order of parameters matters to FastAPI when mixing query and path parameters.

**Answer Y:** Yes, the order of parameters matters to FastAPI when mixing query and path parameters.

---

## r24 (factual)
**Question:** How do include keys with True and nested sets pick fields in model_dump?

**Reference:** include accepts nested dicts and sets: True includes a whole key, nested sets pick sub-fields (e.g. 'address': {'country': {'name'}}), and integer keys such as 0 or -1 select list members. '__all__' applies to every member of a list.

**Answer X:** Including keys with `True` in `model_dump` includes them even if they are part of a set, ensuring proper serialization.

**Answer Y:** By default, `model_dump` includes fields based on their keys, but you can specify them explicitly using `include=True`. For example, to include only the `id`, `username`, and `password` fields, you can use:

```python
print(t.model_dump(exclude={'user', 'value'}))  # {'id': '1234567890'}
```

---

## r25 (how-to)
**Question:** How do I declare a callback router that posts an InvoiceEvent to the customer-supplied URL in FastAPI?

**Reference:** Create an APIRouter and add a post route with path '{$callback_url}/invoices/{$request.body.id}', body: InvoiceEvent and response_model=InvoiceEventReceived (the function body is just pass). Then pass callbacks=invoices_callback_router.routes to the path operation decorator.

**Answer X:** To declare a callback router that posts an InvoiceEvent to the customer-supplied URL in FastAPI, you need to follow these steps:

1. Define a route that handles the creation of an invoice.
2. Use the `invoices_callback_router` attribute to define the callback router.
3. In the callback router, handle the POST request to the external API with the notification of the invoice event.

Here’s how you can implement it:

```python
# Define the route for creating an invoice
@app.post("/invoices/")
async def create_invoice(invoice: Invoice, callback_url: Union[HttpUrl, None] = None):
    """
    Create an invoice.

    This will (let's imagine) let the API user (some external developer) create an
    invoice.

    And this path operation will:
    - Send the invoice to the customer.
    - Collect the money.
    - Send a notification back to the API user (the external developer), as a callback.
      * At

**Answer Y:** To declare a callback router that posts an InvoiceEvent to the customer-supplied URL in FastAPI, you need to follow these steps:

1. **Create the External API**: You already have an external API endpoint defined in FastAPI. Let's call it `create_invoice`.

2. **Define the Callback Router**: Use the `APIRouter` class to define the callback router. Here’s how you can set up the callback router:

   ```python
   from fastapi import APIRouter, HTTPException
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

   @invoices_callback_router.post("/{invoice_id

---

## r26 (comparison)
**Question:** How can I use Starlette as an ASGI toolkit without the full framework?

**Reference:** Starlette components can be used independently: write a raw ASGI app function (scope, receive, send) that builds a response such as PlainTextResponse and awaits response(scope, receive, send), then run it with uvicorn main:app.

**Answer X:** To use Starlette as an ASGI toolkit without the full framework, you can use its components independently. For example, you can use `FastAPI` as a standalone application. Here’s how you can set up a simple Flask-like application using Starlette:

```python
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZIPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.redirect import RedirectMiddleware
from starlette.middleware.temporary import TemporaryRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.redirect import RedirectMiddleware
from starlette.middleware.temporary import TemporaryRedirect

**Answer Y:** To use Starlette as an ASGI toolkit without the full framework, you can install it separately and then use it within your existing project structure.

---

## r27 (factual)
**Question:** Does Pydantic work with mypy without any configuration, and what does the mypy plugin add?

**Reference:** Yes, it works out of the box. The mypy plugin adds Pydantic-specific checks that plain mypy misses, such as a missing field annotation, and a typed __init__ signature for models.

**Answer X:** Yes, Pydantic works with mypy without any configuration. The mypy plugin adds several important Pydantic-specific features that improve its ability to type-check your code. For example, it supports synthesizing a `__init__` method for Pydantic models and dataclasses, and it improves Pydantic's handling of optional fields and dynamic typing.

**Answer Y:** Yes, Pydantic works seamlessly with mypy without any configuration. The mypy plugin adds several important Pydantic-specific features that improve its type checking capabilities.

---

## r28 (how-to)
**Question:** How do I use Tag with a callable discriminator to distinguish an int from a model?

**Reference:** Annotate the union members with Tag('int') and Tag('model') and wrap the Union with Discriminator(callable). The callable returns 'int' for ints, 'model' for dicts or BaseModel instances, and None if no tag is found.

**Answer X:** To use a callable discriminator with a Tag, ensure the discriminator function returns `None` for values not found. This allows the Tag to differentiate between different types of data.

**Answer Y:** To use a callable discriminator with a Tag, ensure the discriminator returns a specific value when the input matches the tag. For example, if you want to differentiate between integers and models, you should return `None` for integer values and the model name for model values.

---

## r29 (comparison)
**Question:** Why must path operation function names be unique if I reuse them as OpenAPI operation IDs?

**Reference:** Because OpenAPI operationIds must be unique. If you set operation_id to the function name (route.name), every path operation function needs a unique name, even across different modules.

**Answer X:** Path operation function names must be unique to avoid conflicts with OpenAPI-generated operation IDs. This ensures that each request handler receives a distinct operation ID, making the client generation process cleaner and more efficient.

**Answer Y:** To ensure uniqueness, you should define a unique identifier for each path operation within your application. This identifier should be a combination of the path operation name and a tag. For example, if you have multiple path operations named `get_items`, you might use `get_items_1` and `get_items_2`. The tag can be anything meaningful, such as the item ID or a random string.

---

## r30 (factual)
**Question:** What does errors() return for a missing field, including loc, msg, input and url?

**Reference:** Each error is a dict with type (e.g. 'missing'), loc (a tuple), msg (e.g. 'Field required'), the input value, and a url pointing to the errors.pydantic.dev page for that error type.

**Answer X:** [
    {
        'type': 'missing',
        'loc': ('items', 1, 'value'),
        'msg': 'Field required',
        'input': {'key': 'baz'},
        'url': 'https://errors.pydantic.dev/2/v/missing',
    }
]

I cannot find this in the provided documentation.

**Answer Y:** [
    {
        'type': 'missing',
        'loc': ('items', 1, 'value'),
        'msg': 'Field required',
        'input': {'key': 'baz'},
        'url': 'https://errors.pydantic.dev/2/v/missing',
    }
]

---

## r31 (how-to)
**Question:** Why should only requirements.txt be copied into the image before the rest of the code in a FastAPI Dockerfile?

**Reference:** Docker caches layers. The requirements file rarely changes, so copying it first lets Docker reuse the cached layers for installing dependencies on rebuilds. The app code, which changes often, is copied later.

**Answer X:** To ensure that the requirements are cached by Docker, only the requirements.txt file should be copied into the image before the rest of the code. This prevents Docker from caching unnecessary files and speeds up the build process.

**Answer Y:** To ensure that the Docker image is built incrementally and uses the cache for dependencies, only the file containing the package requirements (`requirements.txt`) should be copied into the image before the rest of the code. This prevents unnecessary copies and reduces the overall build time.

---

## r32 (comparison)
**Question:** Why can't I declare both Form fields and JSON Body fields in the same path operation?

**Reference:** Because form data is encoded as application/x-www-form-urlencoded (or multipart/form-data with files) instead of application/json, so a body cannot be both. This is part of the HTTP protocol, not a FastAPI limitation.

**Answer X:** Because they are treated differently by the HTTP protocol and the FastAPI framework respectively.

**Answer Y:** Because they are treated differently by FastAPI, which is part of the HTTP protocol.

---

## r33 (factual)
**Question:** Which decorator parameter omits values that were not actually set when returning a model?

**Reference:** response_model_exclude_unset=True in the path operation decorator.

**Answer X:** `response_model_exclude_unset`

**Answer Y:** `response_model_exclude_unset=True`

---

## r34 (how-to)
**Question:** How do I serve static files from a directory in FastAPI with StaticFiles?

**Reference:** Import StaticFiles from fastapi.staticfiles and mount it: app.mount('/static', StaticFiles(directory='static'), name='static').

**Answer X:** To serve static files from a directory in FastAPI with `StaticFiles`, follow these steps:

1. **Import `StaticFiles`:**
   ```python
   from fastapi import FastAPI
   from fastapi.staticfiles import StaticFiles
   ```

2. **Mount a `StaticFiles` instance:**
   ```python
   app.mount("/static", StaticFiles(directory="static"), name="static")
   ```

3. **Configure the app to serve static files:**
   ```python
   @app.get("/")
   async def read_root():
       return {"message": "Hello, World!"}

   if __name__ == "__main__":
       app.run()
   ```

By following these steps, your FastAPI application will automatically serve static files from the specified directory (`/static`) when accessed via the root URL (`/`).

**Answer Y:** To serve static files from a directory in FastAPI with `StaticFiles`, you can import `StaticFiles` and mount it in a specific path. Here’s how you can do it:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
```

In this example, `/static` is the directory where the static files are located. You can access the static files using the URL pattern `/static/<filename>`. For example, to serve the file named `index.html`, you would use `http://localhost:8000/static/index.html`.

---

## r35 (comparison)
**Question:** Is giving root_path to the FastAPI constructor equivalent to the --root-path option of Uvicorn?

**Reference:** Yes. Passing root_path to the FastAPI constructor, e.g. FastAPI(root_path='/api/v1'), is equivalent to passing --root-path to Uvicorn or Hypercorn, which is useful when you cannot provide a command line option.

**Answer X:** Yes, giving root_path to the FastAPI constructor is equivalent to the --root-path option of Uvicorn.

**Answer Y:** Yes, giving `root_path` to the FastAPI constructor is equivalent to setting the `--root-path` option of Uvicorn.

---

## r36 (factual)
**Question:** In the concurrent burgers story, what does the person do while waiting for the order after paying?

**Reference:** They sit at a table with their crush and talk, checking the number on the counter display from time to time, until their number comes up and they collect the burgers.

**Answer X:** They switch 🔀 their attention to their crush, working on that instead.

**Answer Y:** After paying 💸, the person waits for their turn by standing in front of the counter 🕙, so that no one else takes their burgers before them, as there are no numbers for turns.

---

## r37 (comparison)
**Question:** Who normally handles HTTPS for a FastAPI container, and how can Traefik help?

**Reference:** HTTPS is normally handled externally, by another container or tool such as Traefik (which automatically obtains certificates and integrates with Docker and Kubernetes), or by a cloud provider.

**Answer X:** For a FastAPI container, typically HTTPS is handled externally by another tool such as Traefik. Traefik integrates with Docker, Kubernetes, and other platforms, making it easy to set up and configure HTTPS for both the container and the running container.

**Answer Y:** Travis CI automatically handles HTTPS for a FastAPI container. Traefik helps by managing certificates and providing an external HTTPS endpoint for testing purposes.

---

## r38 (how-to)
**Question:** How do I use PlainSerializer to format an integer as a string with thousands separators only in JSON mode?

**Reference:** Annotate int with PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json'). model_dump() keeps 1234 while model_dump(mode='json') gives '1,234'.

**Answer X:** To format an integer as a string with thousands separators only in JSON mode using PlainSerializer, you can pass the `when_used` argument with the value `'json'`. For example:

```python
from typing import Annotated

from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

FancyInt = Annotated[int, PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json')]
```

**Answer Y:** To format an integer as a string with thousands separators only in JSON mode, you can use the following code snippet:

```python
from pydantic import BaseModel, Field
from pydantic.functional_serializers import PlainSerializer

class MyModel(BaseModel):
    x: int

print(MyModel(x=1234).model_dump())
#> {"x": "1,234"}
```

---

## r39 (how-to)
**Question:** How do I keep a union return type annotation like Response or dict without FastAPI trying to build a response model?

**Reference:** Set response_model=None in the path operation decorator. This skips response model generation, so you can keep a Response | dict return annotation for editors and type checkers.

**Answer X:** To keep a union return type annotation like `Response` or `dict` without FastAPI building a response model, you can set `response_model=None`. This allows FastAPI to interpret the union as a single type rather than creating a separate response model.

**Answer Y:** To keep a union return type annotation like `Response` or `dict` without FastAPI building a response model, you can disable the response model generation by setting `response_model=None`. This allows you to specify the actual return type directly in the function definition.

---

## r40 (comparison)
**Question:** Why does Uvicorn not expect requests at /api/v1/app even though the root path is set to /api/v1?

**Reference:** Because Uvicorn expects the proxy to reach it at /app. The proxy is responsible for adding the /api/v1 prefix; root_path only informs the application about it.

**Answer X:** Uvicorn expects requests to be routed to the specified root path because it is designed to handle routes starting with the root path. When you specify a different root path in your FastAPI app, such as `/api/v1`, Uvicorn interprets it differently. It treats the new root path as a separate route, which is why it doesn’t recognize requests to `/api/v1/app`.

**Answer Y:** Uvicorn expects requests at `/api/v1/app` because it uses the `root_path` defined in the FastAPI configuration. The `root_path` is set to `/api/v1`, which means that Uvicorn will look for the `root_path` within the context of the FastAPI app. When you make a request to `/api/v1/app`, Uvicorn tries to match the request against the configured `root_path`. Since the actual path requested is `/api/v1`, Uvicorn doesn't recognize it as a valid path and thus does not forward the request to the appropriate route.

---

## r41 (comparison)
**Question:** What happens when a path operation function is declared with plain def instead of async def?

**Reference:** A plain def function runs in an external threadpool that is awaited, instead of being called directly, so it does not block the server. For trivial compute-only functions async def is actually better.

**Answer X:** When a path operation function is declared with plain `def` instead of `async def`, it runs in an external threadpool that is then awaited, rather than being called directly. This means that the function will block until its completion, potentially leading to higher latency compared to using `async def`.

**Answer Y:** When a path operation function is declared with plain `def` instead of `async def`, it runs in an external threadpool that is then awaited, rather than being called directly. This means that the function will block until its completion, potentially leading to higher latency compared to using `async def`.

---

## r42 (factual)
**Question:** How do union validation errors name each branch when members are annotated with a Tag?

**Reference:** Each branch is labelled with its Tag, so errors are reported as DoubledList.0 and StringsMap instead of generic union branch names.

**Answer X:** When members of a union are annotated with a Tag, the errors are named based on the Tag value. For example, if a Tag is "str", the error will have a type of `str_parsing` and an input value of `'a'`, indicating that the input should be a valid string but was parsed as an integer.

**Answer Y:** When members of a union are annotated with a Tag, they are grouped into branches based on their type. For example, if a union has two members annotated with `Tag('str')`, it will be split into two branches: one for strings and another for other types. The exact number of branches depends on how many tags are applied.

---

## r43 (factual)
**Question:** Which extra dependency do I need to use ORJSONResponse in FastAPI?

**Reference:** orjson (and ujson for UJSONResponse).

**Answer X:** To use ORJSONResponse in FastAPI, you need to install `orjson` via pip. You can do this by running:

```bash
pip install orjson
```

**Answer Y:** To use ORJSONResponse in FastAPI, you need to install the `pydantic-extra-types` and `pydantic-settings` dependencies. You can do this by running the following command in your terminal:

```bash
pip install pydantic-extra-types pydantic-settings
```

---

## r44 (how-to)
**Question:** How can I stop FastAPI from showing the entire docstring of a path operation in the OpenAPI description?

**Reference:** Put a form feed escape (backslash f) in the docstring. FastAPI truncates the OpenAPI description at that point, while other tools such as Sphinx can still use the rest.

**Answer X:** I cannot find this in the provided documentation.

**Answer Y:** To stop FastAPI from displaying the entire docstring of a path operation in the OpenAPI description, you can use the `exclude_from_schema` parameter in the `create_item` function. Set this parameter to `False`. This ensures that only the description is included in the OpenAPI schema, which should prevent the detailed docstrings from being shown in the documentation.

---

## r45 (factual)
**Question:** Where can I check which input types are accepted in strict mode?

**Reference:** In the Conversion Table of the Pydantic documentation.

**Answer X:** To check which input types are accepted in strict mode, refer to the Conversion Table provided in Pydantic documentation.

**Answer Y:** I cannot find this in the provided documentation.

---

## r46 (factual)
**Question:** Do multiple messages in the chat example share a single WebSocket connection?

**Reference:** Yes. All the messages sent and received use the same WebSocket connection.

**Answer X:** No, multiple messages in the chat example do not share a single WebSocket connection. Each message is sent individually to its own WebSocket connection.

**Answer Y:** Yes, multiple messages in the chat example share a single WebSocket connection. Each message is sent individually through its own WebSocket connection, allowing different users to communicate concurrently without blocking each other.

---

## r47 (factual)
**Question:** What timing does Pydantic's validate_json reach on the emoji data benchmark compared to pure Python?

**Reference:** validate_json takes about 1.54 ms on that benchmark, around 3.45 times faster than the pure Python version.

**Answer X:** The benchmark shows that Pydantic's validate_json reaches 5.32 milliseconds, whereas pure Python takes 5.32 milliseconds. This indicates that Pydantic offers significant performance benefits over pure Python for validating emoji data.

**Answer Y:** pydantic: 1.54ms

---

## r48 (how-to)
**Question:** How do I use an alias together with a gt constraint on a validated function argument?

**Reference:** Annotate the parameter as Annotated[int, Field(gt=10, alias='number')] under @validate_call and call it with the alias, e.g. how_many(number=42).

**Answer X:** To use an alias together with a `gt` constraint on a validated function argument, you can define a custom validator that checks the alias against the expected value before applying the constraint. Here's an example:

```python
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

app = FastAPI()

class MyRequest(BaseModel):
    user_id: int

@app.post("/validate")
async def validate(request: MyRequest):
    request_data = request.dict()
    
    # Define a custom validator
    def validate_user_id(user_id: int, user_id_alias: str) -> bool:
        if user_id_alias == "invalid":
            raise ValueError("Invalid user ID alias")
        
        try:
            int(user_id_alias)
        except ValueError:
            raise ValueError(f"Invalid user ID {user_id}: {user_id_alias}")
        
        return True
    
    # Apply the validator to the request data
    result

**Answer Y:** To use an alias together with a `gt` constraint on a validated function argument, you should configure your Pydantic model to allow both `validate_by_alias` and `validate_by_name`. This ensures that the validation logic is applied correctly without conflicts.

---

## r49 (how-to)
**Question:** How can I generate a URL for a named route with request.url_for in Starlette?

**Reference:** Give the Route a name and call request.url_for('name', **path_params). For routes in a named Mount use the '{mount_name}:{route_name}' style.

**Answer X:** To generate a URL for a named route in Starlette, you can use the `url_for` function. For example, if you have a route `/users/{username}` and you want to create a URL for it, you would use:

```python
url = request.url_for("users", username=username)
```

This will return the full URL including the path and query parameters.

**Answer Y:** To generate a URL for a named route in Starlette, you can use the `request.url_for` method. For example, if you have a named route `/users/{username}` and you want to create a URL for it, you would use:

```python
url = request.url_for("users:", username=...)
```

---
