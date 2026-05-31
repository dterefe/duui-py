FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-async/requirements.txt

RUN pip install --no-cache-dir "https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.7.0/de_core_news_sm-3.7.0-py3-none-any.whl" \
    && pip install --no-cache-dir "https://github.com/explosion/spacy-models/releases/download/de_dep_news_trf-3.7.0/de_dep_news_trf-3.7.0-py3-none-any.whl"

WORKDIR /app/examples/spacy-async

EXPOSE 9714

ENTRYPOINT ["uvicorn", "spacy_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
