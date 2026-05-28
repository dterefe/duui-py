#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/stud_homes/s0424382/projects/ttlab/duui-alpha"
cd "$ROOT"
IGNORE_FILE="$(cat /tmp/duui_py_latest_eval_ignorefile)"
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/spacy-legacy-lua/Dockerfile -t localhost/duui-py-spacy-legacy-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/spacy-lua-msgpack/Dockerfile -t localhost/duui-py-spacy-lua-msgpack:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/gazetteer-legacy-lua/Dockerfile -t localhost/duui-py-gazetteer-legacy-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/gazetteer-msgpack-lua/Dockerfile -t localhost/duui-py-gazetteer-msgpack-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/gnfinder-legacy-lua/Dockerfile -t localhost/duui-py-gnfinder-legacy-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/gnfinder-msgpack-lua/Dockerfile -t localhost/duui-py-gnfinder-msgpack-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/taxonerd-legacy-lua/Dockerfile -t localhost/duui-py-taxonerd-legacy-lua:latest duui-py
podman build --ignorefile "$IGNORE_FILE" -f duui-py/examples/taxonerd-msgpack-lua/Dockerfile -t localhost/duui-py-taxonerd-msgpack-lua:latest duui-py
podman images --format '{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}}' | rg 'duui-py-(spacy|taxonerd|gazetteer|gnfinder).*(latest|local|dev|spacy372)' | sort > "$(cat /tmp/duui_py_latest_eval_run_dir)/image_ids.txt"
