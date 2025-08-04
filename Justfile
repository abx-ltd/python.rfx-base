set dotenv-required := true
set dotenv-filename := x"app.env"

APP_NAME := env('APP_NAME', 'rfx-base')
TARGET_ENV := env('TARGET_ENV', 'usr-localhost')

import "../../justlib/pyapp.just"
import "../../justlib/python.just"
import "../../justlib/postgres.just"

# List of just commands
@default:
    just --list

run-local:
    uvicorn app_main:app --host 0.0.0.0 --reload --reload-dir="./src" --reload-dir="../../lib/fluvius"

run-gunicorn:
    gunicorn app_main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers ${GUNICORN_WORKER:-1} \
        --bind localhost:${GUNICORN_PORT:-8000} \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --keep-alive 5

echo-config:
    echo "{{FLUVIUS_CONFIG_FILE}}"

init-db:
    python -m mig.init_db
