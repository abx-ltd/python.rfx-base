from alembic_utils.pg_view import PGView

from .. import SCHEMA


hatchet_workflow_run_view = PGView(
    schema=SCHEMA,
    signature="_hatchet_workflow_run",
    definition="""
    SELECT
        COALESCE(
            (array_agg(hwr._id ORDER BY hwr._created ASC))[1],
            uuid_generate_v4()
        ) AS _id,
        MIN(hwr._created) AS _created,
        MAX(hwr._created) AS _updated,
        NULL::uuid AS _creator,
        NULL::uuid AS _updater,
        NULL::timestamp with time zone AS _deleted,
        gen_random_uuid()::varchar AS _etag,
        (array_agg(hwr._realm ORDER BY hwr._created ASC))[1] AS _realm,
        COALESCE(
            (array_agg(hwr.workflow_name ORDER BY hwr._created ASC)
                FILTER (WHERE hwr.status = 'SUBMITTED'))[1],
            (array_agg(hwr.workflow_name ORDER BY hwr._created ASC))[1]
        ) AS workflow_name,
        hwr.workflow_run_id,
        (array_agg(hwr.labels ORDER BY hwr._created ASC)
            FILTER (WHERE hwr.status = 'SUBMITTED'))[1] AS labels,
        (array_agg(hwr.args ORDER BY hwr._created ASC)
            FILTER (WHERE hwr.status = 'SUBMITTED'))[1] AS args,
        (array_agg(hwr.kwargs ORDER BY hwr._created ASC)
            FILTER (WHERE hwr.status = 'SUBMITTED'))[1] AS kwargs,
        MIN(hwr._created) FILTER (WHERE hwr.status = 'SUBMITTED') AS start_time,
        MAX(hwr._created) FILTER (
            WHERE hwr.status IN ('SUCCESS', 'ERROR', 'CANCELED')
        ) AS end_time,
        COALESCE(
            (array_agg(hwr.status ORDER BY hwr._created DESC)
                FILTER (WHERE hwr.status <> 'SUBMITTED'))[1],
            (array_agg(hwr.status ORDER BY hwr._created DESC))[1]
        ) AS status,
        (array_agg(hwr.result ORDER BY hwr._created DESC)
            FILTER (WHERE hwr.status IN ('SUCCESS', 'ERROR')))[1] AS result,
        (array_agg(hwr.err_message ORDER BY hwr._created DESC)
            FILTER (WHERE hwr.status = 'ERROR'))[1] AS err_message,
        (array_agg(hwr.err_trace ORDER BY hwr._created DESC)
            FILTER (WHERE hwr.status = 'ERROR'))[1] AS err_trace
    FROM ncs_hatchet.hatchet_workflow_run hwr
    WHERE hwr._deleted IS NULL
      AND hwr.workflow_run_id IS NOT NULL
    GROUP BY hwr.workflow_run_id;
    """,
)
