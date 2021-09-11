# slicer-extensions-legacy-webapp

Flask web application implementing legacy REST API for Slicer applications supporting only `Midas_v1`.

## Current deployments

| URL | Description |
|-----|-------------|
| https://slicer.kitware.com/ | Slicer legacy extensions catalog server hosted and maintained by Kitware.|

## Repository layout

This section describes main files and directories available in this repository.

* [server](https://github.com/KitwareMedical/slicer-extensions-legacy-webapp/tree/main/server)

    Flask web application served using uWSGI and expected to be proxied through Nginx.

* [bin](https://github.com/KitwareMedical/slicer-extensions-legacy-webapp/tree/main/bin)

    This directory contains shell scripts for starting/stopping the flask web application and for setting up the
    relevant environments.

    | Name                              | Description |
    |-----------------------------------|-------------|
    | `download-static-assets.sh`       | Download up-to-date static assets from [KitwareMedical/slicer-extensions-webapp@slicer-kitware-com][branch-slicer-kitware-com] branch. |
    | `start`                           | Shell script for starting the download Flask web application. |
    | `stop`                            | Shell script for stopping the download Flask web application. |

[branch-slicer-kitware-com]: https://github.com/KitwareMedical/slicer-extensions-webapp/tree/slicer-kitware-com

## Getting started with development

1. Create a virtual environment and install prerequisites

    ```
    cd slicer-extensions-legacy-webapp
    python -m venv env
    ./env/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
    ```

2. Download up-to-date static assets from [KitwareMedical/slicer-extensions-webapp@slicer-kitware-com][branch-slicer-kitware-com] branch.

    ```
    ./bin/download-static-assets.sh
    ```

3. Setup the startup environment

    ```
    echo "export SLICER_EXTENSIONS_LEGACY_WEBAPP_DEBUG=True" >> ./bin/.start_environment
    ```

4. Start the server
  
    ```
    ./bin/start
    ```

To simultaneously develop the web application frontend and the REST API implemented in
the Flask application, consider the following steps:

1. Start the development server associated with [slicer-extensions-webapp](https://github.com/KitwareMedical/slicer-extensions-webapp)

    ```
    git clone git@github.com:KitwareMedical/slicer-extensions-webapp
    cd slicer-extensions-webapp
    yarn install
    yarn serve
    ```

    Keep track of the development server URL. For example, `http://localhost:8082`.

2. Update the startup environment

    ```
    echo "export FLASK_ENV=development" >> ./bin/.start_environment
    echo "export SLICER_EXTENSIONS_WEBAPP_SERVER_HOST=http://localhost:8082" >> ./bin/.start_environment
    ```

3. Restart the server

    ```
    ./bin/stop
    ./bin/start
    ```

## Startup environment

These variables may be exported in the file `./bin/.start_environment` to customize environment
associated with the `./bin/start` script.

| Variable Name | Description | Default |
|---------------|-------------|---------|
| `FLASK_ENV` | Setting to `development` will proxy assets from `SLICER_EXTENSIONS_WEBAPP_SERVER_HOST`. Supported values are `production` or `development`. | `production` |
| `UWSGI_HTTP_PORT` | Port associated with the uWSGI server running the Flask application. | `53693` |
| `SLICER_EXTENSIONS_LEGACY_WEBAPP_DEBUG` | If `True`, show unhandled exceptions and reload server when code changes. For more details, see [here](https://flask.palletsprojects.com/en/2.0.x/config/#DEBUG). | `False` |
| `SLICER_EXTENSIONS_LEGACY_WEBAPP_HOSTNAME` | URL of the Slicer legacy extensions catalog server. | `http://127.0.0.1:<UWSGI_HTTP_PORT>` |
| `SLICER_EXTENSIONS_WEBAPP_SERVER_HOST` | URL of the host serving [slicer-extensions-webapp](https://github.com/KitwareMedical/slicer-extensions-webapp#readme) used on `FLASK_ENV` is set to `development`. | `http://localhost:8080` |

## History

The original implementation was based on the `slicerpackages` and `slicerappstore` midas plugins
associated with the [midasplatform](https://github.com/midasplatform).

## License

It is covered by the Apache License, Version 2.0:

https://www.apache.org/licenses/LICENSE-2.0

