import flask

from os import environ

from flask import Flask, request, Response, stream_with_context
from requests import get
from werkzeug.datastructures import Headers


IS_DEV = environ["FLASK_ENV"] == "development"
WEBPACK_DEV_SERVER_HOST = environ.get("SLICER_EXTENSIONS_WEBAPP_SERVER_HOST", "http://localhost:8080")

SLICER_PACKAGE_SERVER_APP_ID = "5f4474d0e1d8c75dfc705482"
SLICER_PACKAGE_SERVER_HOST = "https://slicer-packages.kitware.com"


app = Flask(__name__, static_folder='assets')
app.config.from_envvar('SLICER_EXTENSIONS_LEGACY_WEBAPP_SERVER_CONF')


def proxy(host, path):
    # Adapted from https://ajhyndman.medium.com/hot-reloading-with-react-and-flask-b5dae60d9898
    response = get(f"{host}{path}")
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    headers = {
        name: value
        for name, value in response.raw.headers.items()
        if name.lower() not in excluded_headers
    }
    return response.content, response.status_code, headers


def _is_valid_objectid(oid):
    # Inspired from bson.objectid.ObjectId.__validate()
    if not isinstance(oid, str):
        return False
    if not len(oid) == 24:
        return False
    try:
        bytes.fromhex(oid)
    except ValueError:
        return False
    return True


class MidasException(Exception):
    def __init__(self, message, code=None):
        super().__init__()
        self.message = " ".join(filter(bool, message)) if not isinstance(message, str) else message
        self.code = code


@app.errorhandler(MidasException)
def midas_exception(exc):
    http_status = exc.code
    if http_status is None:
        http_status = 400
    return exc.message, http_status


class MidasAPIException(MidasException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@app.errorhandler(MidasAPIException)
def midas_api_exception(exc):
    failure_code = exc.code
    if exc.code is None:
        failure_code = -1
    return {
        "stat": "fail",
        "message": exc.message,
        "code": failure_code,
    }


@app.route("/midas3/api/json")
def midas_api_json():
    method = request.args.get("method", None)

    if method is None:
        raise MidasAPIException("Parameter 'method' must be set.")

    method_function = {
        "midas.slicerpackages.extension.list": midas_slicerpackages_extension_list,
    }.get(method, None)

    if method_function is None:
        raise MidasAPIException(f'Server error. Requested method {method} does not exist.')

    return method_function()


def slicer_package_server_get(route, exception_class, **kwargs):
    result = get(f"{SLICER_PACKAGE_SERVER_HOST}/api/v1{route}", **kwargs)
    app.logger.info(f"GET {result.request.url}")

    if result.status_code not in (200, 201):

        message = None
        if result.headers.get('content-type') == 'application/json':
            message = result.json().get("message", None)

        raise exception_class([
            f"Server Error. Failed to perform GET {result.request.url}.",
            message,
        ], code=result.status_code)

    return result


def midas_slicerpackages_extension_list():
    names_1 = ["extension_id"]
    names_2 = ["arch", "os", "productname", "slicer_revision"]
    params = {name: request.args.get(name, None) for name in names_1 + names_2}

    if all([not value for value in params.values()]):
        raise MidasAPIException(f"Parameters {*names_1,} or parameters {*names_2,} must be set")

    if params["extension_id"] is not None and not _is_valid_objectid(params["extension_id"]):
        raise MidasAPIException(f"Parameter 'extension_id' must be a valid ObjectID. Value is {params['extension_id']}")

    # Retrieve extension metadata
    result = slicer_package_server_get(
        f"/app/{SLICER_PACKAGE_SERVER_APP_ID}/extension",
        MidasAPIException,
        params={
            "extension_id": params["extension_id"],
            "app_revision": params["slicer_revision"],
            "os": params["os"],
            "arch": params["arch"],
            "baseName": params["productname"]
        }
    )

    return {
        "stat": "ok",
        "code": "0",
        "message": "",
        "data": [{
            "extension_id": extension["_id"],
            "item_id": extension["_id"],
            "arch": extension["meta"]["arch"],
            "enabled": "1",
            "category": extension["meta"]["category"],
            "contributors": extension["meta"].get("contributors", ""),
            "date_creation": extension["created"],
            "description": extension["meta"]["description"],
            "icon_url": extension["meta"]["icon_url"],
            "homepage": extension["meta"]["homepage"],
            "name": "{0}.tar.gz".format(extension["name"]),
            "os": extension["meta"]["os"],
            "productname": extension["meta"]["baseName"],
            "repository_type": extension["meta"]["repository_type"],
            "repository_url": extension["meta"]["repository_url"],
            "revision": extension["meta"]["revision"],
            "screenshots": extension["meta"].get("screenshots", ""),
            "slicer_revision": extension["meta"]["app_revision"],
            } for extension in result.json()]
        }


@app.route("/midas3/download")
def download_extension():
    extension_id = request.args.get("items", None)
    if extension_id is None:
        raise MidasException("Parameter 'items' must be set.")

    if not _is_valid_objectid(extension_id):
        raise MidasException(f"Parameter 'items' must be a valid ObjectID. Value is {extension_id}")

    # Retrieve extension files
    result = slicer_package_server_get(f"/item/{extension_id}/files", MidasException)
    file = result.json()[0]

    # Since existing release do not set the QNetworkRequest::FollowRedirectsAttribute
    # to true, we explicitly stream the download through this server.
    req = slicer_package_server_get(f"/file/{file['_id']}/download", MidasException, stream=True)

    headers = Headers()
    headers.set("Content-Disposition", "attachment", filename=file["name"])
    headers.set("Content-Length", file["size"])

    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers['content-type'], headers=headers)


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def getApp(path):
    if IS_DEV:
        return proxy(WEBPACK_DEV_SERVER_HOST, request.path)
    if path.startswith("midas3/slicerappstore"):
        return app.send_static_file("index.html")
    else:
        return app.send_static_file(path)
