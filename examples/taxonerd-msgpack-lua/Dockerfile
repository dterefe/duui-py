FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/taxonerd-msgpack-lua/requirements.txt

ARG TAXONERD_MODEL=en_ner_eco_md
ARG TAXONERD_LINKING=gbif_backbone
ENV TAXONERD_MODEL=$TAXONERD_MODEL
ENV TAXONERD_LINKING=$TAXONERD_LINKING
RUN pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.3.0/en_ner_eco_md-1.0.0.tar.gz \
    && if [ "$TAXONERD_MODEL" = "en_ner_eco_biobert" ]; then \
        pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.3.0/en_ner_eco_biobert-1.0.0.tar.gz; \
    fi

WORKDIR /app/examples/taxonerd-msgpack-lua

EXPOSE 9714

ENTRYPOINT ["uvicorn", "taxonerd_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
