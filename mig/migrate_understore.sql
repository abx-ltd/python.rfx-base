DO
$$
DECLARE
    r RECORD;
    t RECORD;
    e RECORD;
    new_schema TEXT;
    new_table TEXT;
    new_enum TEXT;
BEGIN
    -- Loop through schemas with a dash in their name
    FOR r IN
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'rfx--user'
    LOOP
        new_schema := replace(r.schema_name, '-', '_');
        RAISE NOTICE 'Processing schema "%" -> "%"', r.schema_name, new_schema;

        -- Rename enum types with a dash
        FOR e IN
            SELECT t2.typname
            FROM pg_type t2
            JOIN pg_namespace n2 ON n2.oid = t2.typnamespace
            WHERE n2.nspname = r.schema_name
              AND t2.typtype = 'e'
        LOOP
            new_enum := concat(replace(e.typname, '_', ''), 'enum');
            RAISE NOTICE '  Renaming enum type "%"."%" -> "%"."%"',
                         r.schema_name, e.typname, new_schema, new_enum;

            EXECUTE format('ALTER TYPE %I.%I RENAME TO %I;',
                           r.schema_name, e.typname, new_enum);
        END LOOP;

        -- Rename tables with a dash first
        FOR t IN
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = r.schema_name
              AND (table_name LIKE '%-%' or table_name LIKE '%--%')
        LOOP
            new_table := replace(t.table_name, '-', '_');
            RAISE NOTICE '  Renaming table "%"."%" -> "%"."%"',
                         r.schema_name, t.table_name, new_schema, new_table;

            EXECUTE format('ALTER TABLE %I.%I RENAME TO %I;',
                           r.schema_name, t.table_name, new_table);
        END LOOP;

        -- Finally, rename the schema itself
        RAISE NOTICE 'Renaming schema "%" -> "%"', r.schema_name, new_schema;
        EXECUTE format('ALTER SCHEMA %I RENAME TO %I;',
                       r.schema_name, new_schema);
    END LOOP;
END;
$$;
