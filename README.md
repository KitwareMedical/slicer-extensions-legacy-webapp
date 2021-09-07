# slicer-extensions-legacy-webapp

Flask web application implementing legacy REST API for Slicer applications supporting only `Midas_v1`.

## Current deployments

_Coming soon_

## Repository layout

This section describes main files and directories available in this repository.

* [server](https://github.com/KitwareMedical/slicer-extensions-legacy-webapp/tree/main/server)

    Flask web application served using uWSGI and expected to be proxied through Nginx.

* [bin](https://github.com/KitwareMedical/slicer-extensions-legacy-webapp/tree/main/bin)

    This directory contains shell scripts for starting/stopping the flask web application and for setting up the
    relevant environments.

    | Name                              | Description |
    |-----------------------------------|-------------|
    | `start`                           | Shell script for starting the download Flask web application. |
    | `stop`                            | Shell script for stopping the download Flask web application. |


## Getting started with development

1. Create a virtual environment and install prerequisites

  ```
  cd slicer-extensions-legacy-webapp
  python -m venv env
  ./env/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
  ```

2. Start the server

  ```
  ./bin/start
  ```

## History

The original implementation was based on the `slicerpackages` and `slicerappstore` midas plugins
associated with the [midasplatform](https://github.com/midasplatform).

## License

It is covered by the Apache License, Version 2.0:

https://www.apache.org/licenses/LICENSE-2.0

