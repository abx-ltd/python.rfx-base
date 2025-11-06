import "../../justlib/pyapp.just"
import "../../justlib/python.just"
import "../../justlib/postgres.just"

mod alembic "../../justlib/alembic.just"

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


@create-schema:
    ./manager db create-schema rfx_schema._schema.RFXConnector --force

@drop-schema: print-vars && _drop-schema-confirmed

[confirm("This will drop the database schema for environment (see: {{TARGET_ENV}}). Are you sure?")]
@_drop-schema-confirmed:
    ./manager db drop-schema rfx_schema._schema.RFXConnector --force


@print-vars:
    ./manager show-config ncs_schema --show-sensitive --show-source

    echo ""
    echo "💡 ENVIRONMENT VARIABLES:"
    echo "   - PYTHONPATH = ${PYTHONPATH}"
    echo "   - TARGET_ENV = ${TARGET_ENV}"
