FROM python:3.11-slim

ARG SPACY_MODEL_NAME=de_core_news_sm

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/spacy-legacy-lua/requirements.txt \
    && python -m spacy download "${SPACY_MODEL_NAME}"

WORKDIR /app/examples/spacy-legacy-lua
ENV PYTHONPATH=/app/src
ENV SPACY_MODEL_NAME=${SPACY_MODEL_NAME}
EXPOSE 9714
CMD ["./start.sh"]
