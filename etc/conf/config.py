import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config_utils import toBool  # noqa: E402


DEBUG = toBool(os.environ.get("SLICER_EXTENSIONS_LEGACY_WEBAPP_DEBUG", False))
