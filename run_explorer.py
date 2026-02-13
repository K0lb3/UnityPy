#!/usr/bin/env python3
"""Launch UnityPy Explorer GUI application."""

import sys
import os

# Ensure the project root is in the path so UnityPy and UnityPyExplorer can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from UnityPyExplorer.main import main

if __name__ == "__main__":
    main()
