FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-legacy-lua/requirements.txt \
    && pip install --no-cache-dir "https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.7.0/de_core_news_sm-3.7.0-py3-none-any.whl"

WORKDIR /app/examples/spacy-legacy-lua
EXPOSE 9714
CMD ["./start.sh"]
