FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/taxonerd-msgpack-lua/requirements.txt \
    && pip install --no-cache-dir \
       "scikit-learn>=1.5.0" \
        "scipy==1.10.1" \
       "conllu>=4.0" \
        "joblib>=1.0" \
        "pysbd>=0.3.4" \
        "threadpoolctl>=3.1.0" \
        "nmslib>=1.7.3.6" \
        "textract>=1.6.5" \
    && pip install --no-cache-dir --no-deps "scispacy==0.5.4"

ARG TAXONERD_MODEL=en_ner_eco_md
ARG TAXONERD_LINKING=gbif_backbone
ARG TAXONERD_MODEL_URL=
ENV TAXONERD_MODEL=$TAXONERD_MODEL
ENV TAXONERD_LINKING=$TAXONERD_LINKING
ENV PYTHONPATH=/app/examples/taxonerd-msgpack-lua/vendor:/app/src
RUN pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_md-1.1.0.tar.gz \
    && pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_md_weak-1.1.0.tar.gz \
    && if [ "$TAXONERD_MODEL" = "en_ner_eco_biobert" ]; then \
        pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_biobert-1.1.0.tar.gz \
        && pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_biobert_weak-1.1.0.tar.gz; \
    fi \
    && if [ -n "$TAXONERD_MODEL_URL" ]; then \
        pip install --no-cache-dir "$TAXONERD_MODEL_URL"; \
    fi

WORKDIR /app/examples/taxonerd-msgpack-lua

EXPOSE 9714

ENTRYPOINT ["uvicorn", "taxonerd_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
