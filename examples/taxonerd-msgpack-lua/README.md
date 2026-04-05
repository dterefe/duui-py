# TaxoNERD (duui-py migration)

This is a full annotator-style migration folder including runtime and container scaffolding.

## Files
- taxonerd_annotator.py annotator implementation
- annotator_config.json DUUI descriptor + params + settings
- TypeSystem*.xml UIMA type system
- requirements.txt runtime dependencies
- pyproject.toml package metadata
- Dockerfile container image build
- start.sh local startup helper

## Local run
Run from the example directory:

./start.sh

## Docker build/run
Build from repo root:

docker build -f examples/taxonerd-msgpack-lua/Dockerfile -t taxonerd-msgpack-lua:latest .
docker run --rm -p 9714:9714 taxonerd-msgpack-lua:latest
