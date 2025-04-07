import warnings

from .exceptions import UnityVersionFallbackError, UnityVersionFallbackWarning

FALLBACK_UNITY_VERSION = None
"""The Unity version to use when no version is defined
   by the SerializedFile or its BundleFile.

   You may manually configure this value to a version string, e.g. `2.5.0f5`.
"""

SERIALIZED_FILE_PARSE_TYPETREE = True
"""Determines if the typetree structures for the Object types will be parsed.

   Disabling this will reduce the load time by a lot (half of the time is spend on parsing the typetrees),
   but it will also prevent saving an edited file.
"""


# WARNINGS CONTROL
warnings.simplefilter("once", UnityVersionFallbackWarning)


# GET FUNCTIONS
def get_fallback_version():
    global FALLBACK_UNITY_VERSION

    if not isinstance(FALLBACK_UNITY_VERSION, str):
        raise UnityVersionFallbackError(
            "No valid Unity version found, and the fallback version is not correctly configured. "
            + "Please explicitly set the value of UnityPy.config.FALLBACK_UNITY_VERSION."
        )

    warnings.warn(
        f"No valid Unity version found, defaulting to UnityPy.config.FALLBACK_UNITY_VERSION ({FALLBACK_UNITY_VERSION})",  # noqa: E501
        category=UnityVersionFallbackWarning,
        stacklevel=2,
    )

    return FALLBACK_UNITY_VERSION
