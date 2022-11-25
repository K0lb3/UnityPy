# used when no version is defined by the SerializedFile or its BundleFile
FALLBACK_UNITY_VERSION = "2.5.0f5"
# determines if the typetree structures for the Object types will be parsed
# disabling this will reduce the load time by a lot (half of the time is spend on parsing the typetrees)
#  but it will also prevent saving an edited file
SERIALIZED_FILE_PARSE_TYPETREE = True

# GLOBAL WARNING SUPPRESSION
FALLBACK_VERSION_WARNED = False  # for FALLBACK_UNITY_VERSION


# GET FUNCTIONS
def get_fallback_version():
    global FALLBACK_VERSION_WARNED
    if not FALLBACK_VERSION_WARNED:
        print(
            f"Warning: 0.0.0 version found, defaulting to UnityPy.config.FALLBACK_UNITY_VERSION ({FALLBACK_UNITY_VERSION})"  # noqa: E501
        )
        FALLBACK_VERSION_WARNED = True
    return FALLBACK_UNITY_VERSION
