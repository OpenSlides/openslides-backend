from textwrap import dedent

from openslides_backend.services.postgresql.db_connection_handling import env

openslides_db = env.DATABASE_NAME


def generate_trigger_sql_code(tablenames: tuple[str, ...]) -> str:
    sql: list[str] = []
    for table in tablenames:
        if table != "public.truncate_tables":
            sql.append(
                f"CREATE OR REPLACE TRIGGER {table.split('.')[1]}_create_trigger AFTER INSERT ON {table} FOR EACH STATEMENT EXECUTE FUNCTION store_table_names();"
            )
    return "\n".join(sql)


def generate_remove_all_test_functions(tablenames: tuple[str, ...]) -> str:
    sql: list[str] = []
    for table in tablenames:
        # if table != "public.truncate_tables":
        sql.append(
            f"DROP TRIGGER IF EXISTS {table.split('.')[1]}_create_trigger ON {table};"
        )
    sql.append("DROP TABLE IF EXISTS public.truncate_tables;")
    sql.append("DROP FUNCTION IF EXISTS store_table_names;")
    sql.append("DROP FUNCTION IF EXISTS truncate_testdata_tables;")
    return "\n".join(sql)


def generate_sql_for_test_initiation(tablenames: tuple[str, ...]) -> str:
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
        BEGIN
            IF (SELECT EXISTS (SELECT * FROM truncate_tables))
            THEN
                EXECUTE
                    (SELECT 'TRUNCATE TABLE '
                    || string_agg(tablename, ', ')
                    || ' RESTART IDENTITY CASCADE'
                    FROM   truncate_tables);
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
