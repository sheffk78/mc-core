#!/bin/bash
# thin wrapper: media-struct-preflight.sh delegates to the python gate
exec python3 "$(dirname "$0")/media-struct-preflight.py" "$@"
