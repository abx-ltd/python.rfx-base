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








# ========== Alembic Migration Commands (Schema-Specific) ==========

# Generate alembic migration for specific schema(s)
# Usage: just mig-autogen "message description" [schema]
# Schema options: user, policy, message, or "all" (default)
# Examples:
#   just mig-autogen "add new field"           # All schemas
#   just mig-autogen "add user field" user     # Only user schema
#   just mig-autogen "update tables" user,message  # Multiple schemas
[no-cd]
mig-autogen MESSAGE SCHEMA="all":
    @echo "🔍 Generating migration for schema(s): {{SCHEMA}}"
    ALEMBIC_SCHEMA_FILTER={{SCHEMA}} alembic -c alembic/alembic.ini revision --autogenerate -m "{{MESSAGE}}"

# Apply all pending migrations (optionally filter by schema)
# Usage: just mig-upgrade [revision] [schema]
[no-cd]
mig-upgrade REVISION="head" SCHEMA="all":
    @echo "⬆️  Upgrading migrations for schema(s): {{SCHEMA}}"
    ALEMBIC_SCHEMA_FILTER={{SCHEMA}} alembic -c alembic/alembic.ini upgrade {{REVISION}}

# Rollback migrations (optionally filter by schema)
# Usage: just mig-downgrade [revision] [schema]
[no-cd]
mig-downgrade REVISION="-1" SCHEMA="all":
    @echo "⬇️  Downgrading migrations for schema(s): {{SCHEMA}}"
    ALEMBIC_SCHEMA_FILTER={{SCHEMA}} alembic -c alembic/alembic.ini downgrade {{REVISION}}

# Create new empty migration (optionally for specific schema)
# Usage: just mig-revision "message" [schema]
[no-cd]
mig-revision MESSAGE SCHEMA="all":
    @echo "📝 Creating revision for schema(s): {{SCHEMA}}"
    ALEMBIC_SCHEMA_FILTER={{SCHEMA}} alembic -c alembic/alembic.ini revision -m "{{MESSAGE}}"

# Check current migration version
[no-cd]
mig-current:
    alembic -c alembic/alembic.ini current

# Show migration history
[no-cd]
mig-history:
    alembic -c alembic/alembic.ini history

# Check differences between database and models (optionally for specific schema)
# Usage: just mig-check [schema]
[no-cd]
mig-check SCHEMA="all":
    @echo "🔍 Checking schema(s): {{SCHEMA}}"
    ALEMBIC_SCHEMA_FILTER={{SCHEMA}} alembic -c alembic/alembic.ini check
