FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/gnfinder-msgpack-lua/requirements.txt

WORKDIR /app/examples/gnfinder-msgpack-lua

EXPOSE 9714

ENTRYPOINT ["uvicorn", "gnfinder_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
