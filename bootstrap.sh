#!/usr/bin/env sh

virtualenv -p /usr/bin/python3 venv

if [ "$?" -eq 0 ]; then
    . venv/bin/activate
    pip install -r requirements.txt
    python3 server.py
else
    echo "Ya na know virtualenv? You no Python 3?"
fi