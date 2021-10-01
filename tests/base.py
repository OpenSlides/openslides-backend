import psycopg2


def reset_db():
    """Deletes all mediafiles except for id=2 and id=3 (example data)"""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mediafile_data WHERE id NOT IN (2, 3)")


def get_connection():
    return psycopg2.connect(
        host="media-postgresql",
        port=5432,
        database="openslides",
        user="openslides",
        password="openslides",
    )
