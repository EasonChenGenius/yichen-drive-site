#!/bin/zsh
cd -- "${0:A:h}"
if [[ -x ../../work/.venv-production/bin/python ]]; then
  exec ../../work/.venv-production/bin/python server.py --port 8766
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || exit 1
  .venv/bin/python -m pip install -r requirements-production.txt || exit 1
fi
exec .venv/bin/python server.py --port 8766
