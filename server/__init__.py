import flask

from os import environ

from flask import json, Flask, request, Response, stream_with_context
from requests import get


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


@app.route("/midas3/api/json")
def midas_api_json():
    method = request.args.get("method", None)
    if method == "midas.slicerpackages.extension.list":
        return midas_slicerpackages_extension_list()
    else:
        return flask.abort(404)


def midas_slicerpackages_extension_list():
    extension_id = request.args.get("extension_id", None)
    app.logger.info("extension_id [%s]" % extension_id)

    arch = request.args.get("arch", None)
    app.logger.info("arch [%s]" % arch)

    operating_system = request.args.get("os", None)
    app.logger.info("operating_system [%s]" % operating_system)

    productname = request.args.get("productname", None)
    app.logger.info("productname [%s]" % productname)

    slicer_revision = request.args.get("slicer_revision", None)
    app.logger.info("slicer_revision [%s]" % slicer_revision)

    if extension_id is None and not all([arch, operating_system, productname, slicer_revision]):
        return flask.abort(404)

    # Retrieve extension metadata
    url = "{host}/api/v1/app/{app_id}/extension".format(
        host=SLICER_PACKAGE_SERVER_HOST,
        app_id=SLICER_PACKAGE_SERVER_APP_ID)
    params = {
        "extension_id": extension_id,
        "app_revision": slicer_revision,
        "os": operating_system,
        "arch": arch,
        "baseName": productname
    }
    app.logger.info("GET {url}?{params}".format(url=url, params=params))
    result = get(url, params)
    if result.status_code not in (200, 201):
        return flask.abort(404)

    return json.dumps({
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
        })


@app.route("/midas3/download")
def download_extension():
    extension_id = request.args.get("items", None)
    if extension_id is None:
        return flask.abort(404)

    # Retrieve extension files
    url = "{host}/api/v1/item/{extension_id}/files".format(
        host=SLICER_PACKAGE_SERVER_HOST,
        extension_id=extension_id)
    app.logger.info("GET %s" % url)
    result = get(url)
    if result.status_code not in (200, 201):
        return flask.abort(404)
    file_id = result.json()[0]['_id']

    # Set download URL
    download_url = "{host}/api/v1/file/{file_id}/download".format(
        host=SLICER_PACKAGE_SERVER_HOST,
        file_id=file_id)
    app.logger.info("GET %s" % download_url)

    # Since existing release do not set the QNetworkRequest::FollowRedirectsAttribute
    # to true, we explicitly stream the download through this server.
    req = get(download_url, stream=True)
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024)),
        content_type=req.headers['content-type'])


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def getApp(path):
    if IS_DEV:
        return proxy(WEBPACK_DEV_SERVER_HOST, request.path)
    if path.startswith("midas3/slicerappstore"):
        return app.send_static_file("index.html")
    else:
        return app.send_static_file(path)
