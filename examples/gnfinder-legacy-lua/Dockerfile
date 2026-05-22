FROM golang:1.23 AS gnfinder-builder
RUN go install github.com/gnames/gnfinder@latest

FROM python:3.11-slim

WORKDIR /app
COPY . /app
COPY --from=gnfinder-builder /go/bin/gnfinder /usr/local/bin/gnfinder

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gnfinder-legacy-lua/requirements.txt

WORKDIR /app/examples/gnfinder-legacy-lua
ENV PYTHONPATH=/app/src
EXPOSE 9714
CMD ["./start.sh"]
