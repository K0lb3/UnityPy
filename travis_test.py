#!/usr/bin/env python

import sys
from platform import uname
print("Python {}.{}.{} on".format(*sys.version_info) + " {0} {4}: {5}".format(*uname()))

import UnityPy

am = UnityPy.AssetsManager()

print("👌")