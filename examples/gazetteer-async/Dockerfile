FROM docker.texttechnologylab.org/gazetteer-rs/biofid:latest AS backend

FROM python:3.11-slim

WORKDIR /app

COPY . /app
COPY --from=backend /app/gazetteer /app/gazetteer
COPY --from=backend /app/config.toml /app/config.toml
COPY --from=backend /app/resources /app/resources

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gazetteer-async/requirements.txt

WORKDIR /app/examples/gazetteer-async

ENTRYPOINT ["sh", "-c", "exec uvicorn ${DUUI_PY_APP:-gazetteer_annotator:app} --host ${DUUI_PY_HOST:-0.0.0.0} --port ${DUUI_PY_PORT:-9714} \"$@\"", "--"]
