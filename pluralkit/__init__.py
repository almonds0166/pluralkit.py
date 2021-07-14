
from .v1.client import Client
from .v1.models import (
    Member,
    System,
    ProxyTag,
    ProxyTags,
    Switch,
    Privacy,
    Timestamp,
    Color,
    Birthday,
    Timezone,
    Message,
)
from .v1 import errors
from .__version__ import version_info, __version__

__title__ = "pluralkit"
__author__ = "Madison Landry, Alyx Warner"
__copyright__ = "Copyright 2021-present Madison Landry, Alyx Warner"