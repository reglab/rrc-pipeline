# Default recipe to run when just is called without arguments
default:
    just --list

# Install all dependencies
install:
    cd backend && uv venv --python 3.11 && uv sync


docker-build:
    docker build -t ghcr.io/reglab/rrc-pipeline:latest -f backend/Dockerfile .

docker-push:
    docker push ghcr.io/reglab/rrc-pipeline:latest



# Run pre-commit hooks
lint:
    pre-commit run --all-files
