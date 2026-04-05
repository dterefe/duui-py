# Semantic Role Labeling (duui-py migration)

This is a full annotator-style migration folder including runtime and container scaffolding.

## Files
- srl_annotator.py annotator implementation
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

docker build -f examples/srl-msgpack-lua/Dockerfile -t srl-msgpack-lua:latest .
docker run --rm -p 9714:9714 srl-msgpack-lua:latest
