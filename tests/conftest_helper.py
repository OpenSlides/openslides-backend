from textwrap import dedent

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.services.postgresql.db_connection_handling import env

openslides_db = env.DATABASE_NAME


def generate_trigger_sql_code(tablenames: tuple[str, ...]) -> str:
    sql: list[str] = []
    for table in tablenames:
        sql.append(
            f"CREATE OR REPLACE TRIGGER {table.split('.')[1]}_create_trigger AFTER INSERT ON {table} FOR EACH STATEMENT EXECUTE FUNCTION store_table_names();"
        )
    return "\n".join(sql)


def generate_remove_all_test_functions() -> str:
    return """
    DROP TABLE IF EXISTS public.truncate_tables;
    DROP FUNCTION IF EXISTS store_table_names CASCADE;
    DROP FUNCTION IF EXISTS truncate_testdata_tables CASCADE;
    """


def generate_sql_for_test_initiation(tablenames: tuple[str, ...]) -> str:
    MigrationHelper.load_migrations()
    return dedent(
        f"""
        CREATE TABLE IF NOT EXISTS truncate_tables (
            id int,
            tablename varchar(256) UNIQUE
        );

        CREATE OR REPLACE FUNCTION store_table_names() RETURNS TRIGGER AS $$
        DECLARE composed_name varchar;
        BEGIN
            composed_name = TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME;
            INSERT INTO truncate_tables (tablename) VALUES (composed_name) ON CONFLICT (tablename) DO NOTHING;
            return NEW;
        END;
        $$ LANGUAGE plpgsql;

        {generate_trigger_sql_code(tablenames)}

        CREATE OR REPLACE FUNCTION truncate_testdata_tables() RETURNS void AS $$
        DECLARE
            t_names CURSOR FOR
                SELECT tablename FROM truncate_tables;
            s_names CURSOR FOR
                SELECT relname FROM pg_class WHERE relkind = 'S' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
        BEGIN
            FOR t_name in t_names LOOP
                EXECUTE 'DELETE FROM ' || t_name.tablename || ' CASCADE';
            END LOOP;
            FOR s_name in s_names LOOP
                PERFORM setval(s_name.relname::regclass, 1, false);
            END LOOP;
            DELETE FROM truncate_tables;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION init_table_contents() RETURNS void AS $$
        BEGIN
            INSERT INTO version (migration_index, migration_state)
            VALUES ({MigrationHelper.get_backend_migration_index()}, '{MigrationState.FINALIZED}')
            ON CONFLICT (migration_index) DO UPDATE SET migration_state = EXCLUDED.migration_state;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
