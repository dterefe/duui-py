FROM docker.texttechnologylab.org/gazetteer-rs/biofid:latest AS backend

FROM python:3.11-slim

WORKDIR /app
COPY . /app
COPY --from=backend /app/gazetteer /app/gazetteer
COPY --from=backend /app/config.toml /app/config.toml
COPY --from=backend /app/resources /app/resources

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gazetteer-legacy-lua/requirements.txt

WORKDIR /app/examples/gazetteer-legacy-lua
EXPOSE 9714
CMD ["./start.sh"]
