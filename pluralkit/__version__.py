
from collections import namedtuple

VersionInfo = namedtuple("VersionInfo", "major minor build")
version_info = VersionInfo(
    major=1,
    minor=0,
    build=1,
)

__version__ = f"{version_info.major}.{version_info.minor}.{version_info.build}"
