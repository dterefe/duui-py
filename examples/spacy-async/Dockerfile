FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-async/requirements.txt

RUN pip install --no-cache-dir "https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.7.0/de_core_news_sm-3.7.0-py3-none-any.whl" \
    && pip install --no-cache-dir "https://github.com/explosion/spacy-models/releases/download/de_dep_news_trf-3.7.0/de_dep_news_trf-3.7.0-py3-none-any.whl"

WORKDIR /app/examples/spacy-async

ENTRYPOINT ["sh", "-c", "exec uvicorn ${DUUI_PY_APP:-spacy_annotator:app} --host ${DUUI_PY_HOST:-0.0.0.0} --port ${DUUI_PY_PORT:-9714} \"$@\"", "--"]
