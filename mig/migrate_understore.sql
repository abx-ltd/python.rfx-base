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
    FOR r IN
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name IN ('rfx--user', 'rfx--message')
    LOOP
        -- Normalize schema name to snake_case.
        new_schema := lower(r.schema_name);
        new_schema := regexp_replace(new_schema, '[^a-z0-9_]+', '_', 'g');
        new_schema := regexp_replace(new_schema, '__+', '_', 'g');
        new_schema := trim(both '_' FROM new_schema);
        RAISE NOTICE 'Processing schema "%" -> "%"', r.schema_name, new_schema;

        FOR e IN
            SELECT t2.typname
            FROM pg_type t2
            JOIN pg_namespace n2 ON n2.oid = t2.typnamespace
            WHERE n2.nspname = r.schema_name
              AND t2.typtype = 'e'
        LOOP
            new_enum := lower(e.typname);
            new_enum := regexp_replace(new_enum, '[^a-z0-9_]+', '_', 'g');
            new_enum := regexp_replace(new_enum, '__+', '_', 'g');
            new_enum := trim(both '_' FROM new_enum);
            IF new_enum <> e.typname THEN
                RAISE NOTICE '  Renaming enum type "%"."%" -> "%"."%"',
                             r.schema_name, e.typname, new_schema, new_enum;

                EXECUTE format('ALTER TYPE %I.%I RENAME TO %I;',
                               r.schema_name, e.typname, new_enum);
            END IF;
        END LOOP;

        FOR t IN
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = r.schema_name
        LOOP
            new_table := lower(t.table_name);
            new_table := regexp_replace(new_table, '[^a-z0-9_]+', '_', 'g');
            new_table := regexp_replace(new_table, '__+', '_', 'g');
            new_table := trim(both '_' FROM new_table);
            IF new_table <> t.table_name THEN
                RAISE NOTICE '  Renaming table "%"."%" -> "%"."%"',
                             r.schema_name, t.table_name, new_schema, new_table;

                EXECUTE format('ALTER TABLE %I.%I RENAME TO %I;',
                               r.schema_name, t.table_name, new_table);
            END IF;
        END LOOP;

        IF new_schema <> r.schema_name THEN
            RAISE NOTICE 'Renaming schema "%" -> "%"', r.schema_name, new_schema;
            EXECUTE format('ALTER SCHEMA %I RENAME TO %I;',
                           r.schema_name, new_schema);
        END IF;
    END LOOP;
END;
$$;
