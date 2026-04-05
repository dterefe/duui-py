FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -e /app \
    && pip install --no-cache-dir -r /app/examples/whisper-msgpack-lua/requirements.txt

WORKDIR /app/examples/whisper-msgpack-lua

EXPOSE 9714

ENTRYPOINT ["uvicorn", "whisper_annotator:app", "--host", "0.0.0.0", "--port", "9714"]
CMD ["--workers", "1"]
