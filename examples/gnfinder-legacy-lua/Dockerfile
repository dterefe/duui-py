FROM docker.io/gnames/gnfinder:latest AS gnfinder-backend

FROM python:3.11-slim

WORKDIR /app
COPY . /app
COPY --from=gnfinder-backend /bin/gnfinder /usr/local/bin/gnfinder

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gnfinder-legacy-lua/requirements.txt

WORKDIR /app/examples/gnfinder-legacy-lua
ENV PYTHONPATH=/app/src
EXPOSE 9714
CMD ["./start.sh"]
