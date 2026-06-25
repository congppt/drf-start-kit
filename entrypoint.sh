#!/bin/sh
set -e

mkdir -p /dist/logs
chown -R appuser:appuser /dist/logs

# Gunicorn 25+ creates a control socket under $HOME/.gunicorn; appuser has no writable home.
exec gosu appuser env HOME=/tmp "$@"