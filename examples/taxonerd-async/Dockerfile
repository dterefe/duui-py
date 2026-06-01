FROM python:3.10-slim

WORKDIR /app

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.10/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH}

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/taxonerd-async/requirements.txt \
    && pip install --no-cache-dir \
       "scikit-learn>=1.5.0" \
        "scipy==1.10.1" \
       "conllu>=4.0" \
        "joblib>=1.0" \
        "pysbd>=0.3.4" \
        "threadpoolctl>=3.1.0" \
        "nmslib>=1.7.3.6" \
        "textract>=1.6.5" \
        "torch>=2.0.0" \
        "cupy-cuda13x>=13.6.0" \
    && pip install --no-cache-dir --no-deps "scispacy==0.5.4" \
    && pip install --no-cache-dir --no-deps git+https://github.com/abrami/taxonerd

RUN pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_md-1.1.0.tar.gz \
    && pip install --no-cache-dir https://github.com/nleguillarme/taxonerd/releases/download/v1.5.4/en_ner_eco_md_weak-1.1.0.tar.gz

WORKDIR /app/examples/taxonerd-async

EXPOSE 9714

ENTRYPOINT ["uvicorn", "taxonerd_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
