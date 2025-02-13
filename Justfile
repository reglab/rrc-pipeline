# Default recipe to run when just is called without arguments
default:
    just --list

# Install all dependencies
install:
    cd backend && uv venv --python 3.11 && uv sync
    cd frontend && pnpm install

# Start the FastAPI backend development server
api *ARGS:
    cd backend && uv run fastapi dev blank/api/main.py --host 0.0.0.0 --port 8101 {{ARGS}}

# Start the frontend development server
frontend *ARGS:
    cd frontend && pnpm dev --host 0.0.0.0 --port 5185 {{ARGS}}

# Build the frontend for production
build:
    cd frontend && pnpm build

# Regenerate the OpenAPI client
openapi *HOST:
    cd frontend && pnpm run openapi {{HOST}}

# Run pre-commit hooks
lint:
    pre-commit run --all-files

editor := env_var_or_default("EDITOR", "vim")

env:
    #!/usr/bin/env fish
    if not test -f .env
        echo "No .env file found, creating from template.env"
        cp template.env .env
    end
    {{editor}} .env

# Generate a migration with the provided message
migrate *ARGS:
    #!/usr/bin/env fish
    cd backend
    and uv run alembic revision --autogenerate -m "{{ARGS}}"
    and echo (set_color yellow)"Run "(set_color cyan)"just migrate-up"(set_color yellow)" to apply the migration."(set_color normal)

# Apply all migrations
migrate-up:
    cd backend && uv run alembic upgrade head


# Rollback the last migration
migrate-down:
    cd backend && uv run alembic downgrade -1
