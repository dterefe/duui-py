FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-lua-msgpack/requirements.txt

WORKDIR /app/examples/spacy-lua-msgpack

EXPOSE 9714

ENTRYPOINT ["uvicorn", "spacy_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
