#!/bin/sh
# Double-click in Finder to toggle all Macropad attention notifications.
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd) || exit 1
exec "$task_root/build/host-venv/bin/python" "$task_root/firmware/host/claude_alert.py" toggle
