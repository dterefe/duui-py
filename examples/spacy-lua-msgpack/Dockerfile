FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-lua-msgpack/requirements.txt

ARG SPACY_MODEL_NAME=de_dep_news_trf
ARG SPACY_MODEL_LANG=de
ARG TEXTIMAGER_SPACY_VARIANT=
ENV SPACY_MODEL_NAME=$SPACY_MODEL_NAME
ENV SPACY_MODEL_LANG=$SPACY_MODEL_LANG
ENV TEXTIMAGER_SPACY_SINGLE_MODEL=$SPACY_MODEL_NAME
ENV TEXTIMAGER_SPACY_SINGLE_MODEL_LANG=$SPACY_MODEL_LANG
ENV TEXTIMAGER_SPACY_VARIANT=$TEXTIMAGER_SPACY_VARIANT
RUN python -m spacy download "$SPACY_MODEL_NAME"

WORKDIR /app/examples/spacy-lua-msgpack

EXPOSE 9714

ENTRYPOINT ["uvicorn", "spacy_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
