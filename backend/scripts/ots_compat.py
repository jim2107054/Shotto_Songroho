"""
Windows compatibility wrapper for the OpenTimestamps CLI.
"""

import ctypes.util
import os
import sys
from pathlib import Path


def _patch_openssl_lookup() -> None:
    original_find_library = ctypes.util.find_library
    candidates = [
        os.environ.get("OTS_SSL_DLL"),
        r"C:\Program Files\Git\mingw64\bin\libcrypto-3-x64.dll",
        r"C:\Program Files\Cisco Packet Tracer 9.0.1\bin\libcrypto-3-x64.dll",
    ]
    ssl_path = next((path for path in candidates if path and Path(path).exists()), None)
    if not ssl_path:
        return

    def find_library(name):
        if name in {"ssl", "ssl.35", "libeay32"}:
            return ssl_path
        return original_find_library(name)

    ctypes.util.find_library = find_library


_patch_openssl_lookup()

from otsclient.ots import main  # noqa: E402

if __name__ == "__main__":
    main()
