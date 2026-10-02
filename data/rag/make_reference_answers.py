"""Reference answers for the 50 RAG test questions (written by Claude from each question's gold passage,
before any system output existed). Run once: python data/rag/make_reference_answers.py"""
import json
from pathlib import Path

HERE = Path(__file__).parent

A = {
    "r00": "Yes. A Response parameter can also be declared in dependencies, where you can set headers and cookies on it just as in a path operation function; FastAPI extracts them from that temporary response.",
    "r01": "Create a TypeAdapter for list[User], where User is a TypedDict, and call validate_python on the list of dicts. Values are coerced (id '3' becomes 3) and invalid items raise a ValidationError naming the index and field, like 0.id.",
    "r02": "Because writing or copying the code, editing it and running it locally in your editor shows the real benefits of FastAPI: how little code you write, the type checks and the autocompletion.",
    "r03": "Microsoft (ML services, some integrated into Windows and Office), Uber (a REST server for predictions for Ludwig) and Netflix (the open-source crisis management framework Dispatch, built with FastAPI).",
    "r04": "Use the validate_call decorator. Keyword-only parameters come after a bare * (def f(*, a, b=2)); positional-only parameters come before a / (def f(a, b=2, /)); *args and **kwargs are supported too.",
    "r05": "pip installs wheels compiled for your local platform, which may not be compatible with the Lambda environment. Install with --platform (e.g. manylinux2014_x86_64), --python-version, --implementation cp and --only-binary=:all: matching the Lambda runtime.",
    "r06": "OpenAPI 3 (YAML/JSON), JSON Schema, JSON/YAML/CSV data and Python dictionaries (converted to JSON Schema) and GraphQL schemas.",
    "r07": "Declare a parameter of type Response in the path operation function and set response.status_code on it, e.g. status.HTTP_201_CREATED. FastAPI takes the status code from that temporary response, and response_model still filters the returned data.",
    "r08": "Call httpx.get(url), raise_for_status(), then pass response.json() to User.model_validate() on a BaseModel such as User(id, name, email). For a list of users use a TypeAdapter.",
    "r09": "Logfire is an observability platform from the Pydantic team. Its Pydantic integration shows the data passing through your models and gives analytics on validations. You set up an account, install the SDK and instrument your project.",
    "r10": "Pass the HTTPEndpoint class itself, not an instance, to a Route, e.g. Route('/', Homepage), in the routes list of the Starlette app. Methods the class does not implement return 405 Method Not Allowed.",
    "r11": "In lax mode '2020-01-01T12:00' is parsed into a datetime and 'home' into bytes. With strict=True both fields fail, since Python str input is not a datetime or bytes instance (validating from JSON still works).",
    "r12": "The Starlette class ties together all the other functionality: routes (Route, Mount, WebSocketRoute), static files, lifespan and so on, configured in a single application object.",
    "r13": "Pass dependencies=[Depends(verify_token), Depends(verify_key)] to the path operation decorator. Each dependency reads a header (X-Token, X-Key) with Header() and raises an HTTPException if it is invalid.",
    "r14": "frozenset is treated like a set (a list in requests is deduplicated into a set; responses convert it to a list; the schema marks uniqueItems). bytes is treated as str with binary format in the schema. Decimal is handled like a float.",
    "r15": "Yes. strict mode works with TypeAdapter for dataclasses. Passing a plain dict with strict=True fails with 'Input should be an instance of MyDataclass'.",
    "r16": "Add intersphinx_mapping = {'pydantic': ('https://docs.pydantic.dev/latest', None)} to your Sphinx configuration (use dev instead of latest for the latest main build).",
    "r17": "No. tokenUrl only declares which URL the client should use to get the token, which is used by OpenAPI and the interactive docs. You still have to create the actual path operation.",
    "r18": "Schema generation inspects app.routes and uses the docstrings or other attributes of the endpoints to build the schema. Starlette includes a simple implementation that generates OpenAPI from docstrings, but it is not tied to any particular tooling.",
    "r19": "Write a class with an active_connections list, an async connect that accepts and appends the websocket, a disconnect that removes it, send_personal_message, and a broadcast method that loops over all connections sending the text.",
    "r20": "pydantic-core (the Rust validation core), typing-extensions and annotated-types. Python 3.9+ with pip is enough.",
    "r21": "An httpx AsyncClient created with ASGITransport(app=app) and a base_url, used as await ac.get('/') inside an async test marked with @pytest.mark.anyio.",
    "r22": "Subclass Convertor with a regex, convert() and to_string() methods, register it with register_url_convertor('datetime', DateTimeConvertor()), then use it in paths such as '/history/{date:datetime}'.",
    "r23": "No. FastAPI detects parameters by name, type and default declarations (Query, Path), not by order, so the required query parameter q can come first (or you can use * as the first parameter). Annotated avoids the problem.",
    "r24": "include accepts nested dicts and sets: True includes a whole key, nested sets pick sub-fields (e.g. 'address': {'country': {'name'}}), and integer keys such as 0 or -1 select list members. '__all__' applies to every member of a list.",
    "r25": "Create an APIRouter and add a post route with path '{$callback_url}/invoices/{$request.body.id}', body: InvoiceEvent and response_model=InvoiceEventReceived (the function body is just pass). Then pass callbacks=invoices_callback_router.routes to the path operation decorator.",
    "r26": "Starlette components can be used independently: write a raw ASGI app function (scope, receive, send) that builds a response such as PlainTextResponse and awaits response(scope, receive, send), then run it with uvicorn main:app.",
    "r27": "Yes, it works out of the box. The mypy plugin adds Pydantic-specific checks that plain mypy misses, such as a missing field annotation, and a typed __init__ signature for models.",
    "r28": "Annotate the union members with Tag('int') and Tag('model') and wrap the Union with Discriminator(callable). The callable returns 'int' for ints, 'model' for dicts or BaseModel instances, and None if no tag is found.",
    "r29": "Because OpenAPI operationIds must be unique. If you set operation_id to the function name (route.name), every path operation function needs a unique name, even across different modules.",
    "r30": "Each error is a dict with type (e.g. 'missing'), loc (a tuple), msg (e.g. 'Field required'), the input value, and a url pointing to the errors.pydantic.dev page for that error type.",
    "r31": "Docker caches layers. The requirements file rarely changes, so copying it first lets Docker reuse the cached layers for installing dependencies on rebuilds. The app code, which changes often, is copied later.",
    "r32": "Because form data is encoded as application/x-www-form-urlencoded (or multipart/form-data with files) instead of application/json, so a body cannot be both. This is part of the HTTP protocol, not a FastAPI limitation.",
    "r33": "response_model_exclude_unset=True in the path operation decorator.",
    "r34": "Import StaticFiles from fastapi.staticfiles and mount it: app.mount('/static', StaticFiles(directory='static'), name='static').",
    "r35": "Yes. Passing root_path to the FastAPI constructor, e.g. FastAPI(root_path='/api/v1'), is equivalent to passing --root-path to Uvicorn or Hypercorn, which is useful when you cannot provide a command line option.",
    "r36": "They sit at a table with their crush and talk, checking the number on the counter display from time to time, until their number comes up and they collect the burgers.",
    "r37": "HTTPS is normally handled externally, by another container or tool such as Traefik (which automatically obtains certificates and integrates with Docker and Kubernetes), or by a cloud provider.",
    "r38": "Annotate int with PlainSerializer(lambda x: f'{x:,}', return_type=str, when_used='json'). model_dump() keeps 1234 while model_dump(mode='json') gives '1,234'.",
    "r39": "Set response_model=None in the path operation decorator. This skips response model generation, so you can keep a Response | dict return annotation for editors and type checkers.",
    "r40": "Because Uvicorn expects the proxy to reach it at /app. The proxy is responsible for adding the /api/v1 prefix; root_path only informs the application about it.",
    "r41": "A plain def function runs in an external threadpool that is awaited, instead of being called directly, so it does not block the server. For trivial compute-only functions async def is actually better.",
    "r42": "Each branch is labelled with its Tag, so errors are reported as DoubledList.0 and StringsMap instead of generic union branch names.",
    "r43": "orjson (and ujson for UJSONResponse).",
    "r44": "Put a form feed escape (backslash f) in the docstring. FastAPI truncates the OpenAPI description at that point, while other tools such as Sphinx can still use the rest.",
    "r45": "In the Conversion Table of the Pydantic documentation.",
    "r46": "Yes. All the messages sent and received use the same WebSocket connection.",
    "r47": "validate_json takes about 1.54 ms on that benchmark, around 3.45 times faster than the pure Python version.",
    "r48": "Annotate the parameter as Annotated[int, Field(gt=10, alias='number')] under @validate_call and call it with the alias, e.g. how_many(number=42).",
    "r49": "Give the Route a name and call request.url_for('name', **path_params). For routes in a named Mount use the '{mount_name}:{route_name}' style.",
}

questions = [json.loads(line)["qid"] for line in open(HERE / "rag_questions.jsonl", encoding="utf-8")]
assert set(A) == set(questions), set(A) ^ set(questions)
with open(HERE / "reference_answers.jsonl", "w", encoding="utf-8") as f:
    for qid in sorted(A):
        f.write(json.dumps({"qid": qid, "answer": A[qid]}, ensure_ascii=False) + "\n")
print(len(A), "reference answers written")
