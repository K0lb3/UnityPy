__version__ = "1.22.3"

from .environment import Environment as Environment
from .helpers.ArchiveStorageManager import (
    set_assetbundle_decrypt_key as set_assetbundle_decrypt_key,
)

load = Environment

# backward compatibility
AssetsManager = Environment
