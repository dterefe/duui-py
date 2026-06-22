FROM docker.io/gnames/gnfinder:latest AS gnfinder-backend

FROM python:3.11-slim

WORKDIR /app

COPY --from=gnfinder-backend /bin/gnfinder /usr/local/bin/gnfinder

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gnfinder-async/requirements.txt

WORKDIR /app/examples/gnfinder-async

ENTRYPOINT ["sh", "-c", "exec uvicorn ${DUUI_PY_APP:-gnfinder_annotator:app} --host ${DUUI_PY_HOST:-0.0.0.0} --port ${DUUI_PY_PORT:-9714} \"$@\"", "--"]
