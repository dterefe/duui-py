FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/taxonerd-legacy-lua/requirements.txt

WORKDIR /app/examples/taxonerd-legacy-lua
ENV PYTHONPATH=/app/src
EXPOSE 9714
CMD ["./start.sh"]
