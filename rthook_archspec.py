"""PyInstaller runtime hook: fix archspec JSON data path.

archspec resolves its JSON data relative to schema.py (__file__),
but PyInstaller places code in Frameworks/ and data in Resources/.
We set the ARCHSPEC_CPU_DIR env var so archspec finds its JSON files.
"""
import os
import sys

if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    archspec_json_dir = os.path.join(bundle_dir, 'archspec', 'json', 'cpu')
    if os.path.isdir(archspec_json_dir):
        os.environ['ARCHSPEC_CPU_DIR'] = archspec_json_dir
