FROM docker.texttechnologylab.org/duui-geonames-fst/de:latest AS fst-backend
FROM docker.texttechnologylab.org/gazetteer-rs/geonames:latest AS text-backend

FROM python:3.11-slim

WORKDIR /app

COPY . /app
COPY --from=fst-backend /app/geonames-fst /app/geonames-fst
COPY --from=fst-backend /app/data /app/data
COPY --from=fst-backend /app/resources /app/resources
COPY --from=text-backend /app/gazetteer /app/geonames-gazetteer/gazetteer
COPY --from=text-backend /app/config.toml /app/geonames-gazetteer/config.toml
COPY --from=text-backend /app/resources /app/geonames-gazetteer/resources

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/geonames-msgpack-lua/requirements.txt

WORKDIR /app/examples/geonames-msgpack-lua

EXPOSE 9714

ENTRYPOINT ["uvicorn", "geonames_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
