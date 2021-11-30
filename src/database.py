import psycopg2

from .cache import LRUCache
from .exceptions import NotFoundError, ServerError


class Database:
    def __init__(self, app):
        self.config = app.config
        self.logger = app.logger
        self.connection = None
        self.cache_mediafile = LRUCache(self.logger, 20)
        self.cache_resource = LRUCache(self.logger, 20)

    def get_file(self, file_id, file_type):
        if file_type == "mediafile" and self.cache_mediafile.has_media_id(file_id):
            return self.cache_mediafile.get_media(file_id)
        elif file_type == "resource" and self.cache_resource.has_media_id(file_id):
            return self.cache_resource.get_media(file_id)
        while True:
            connection = self.get_connection()
            try:
                with connection:
                    media = self._query(connection, file_id, file_type)
                    if file_type == "mediafile":
                        self.cache_mediafile.set_media(file_id, media)
                    elif file_type == "resource":
                        self.cache_resource.set_media(file_id, media)
                    return media
            except psycopg2.InterfaceError:
                if self.connection:
                    self.connection.close()
                self.connection = None
                self.logger.info("Database connection has been reset. " "Reconnect...")
            except psycopg2.Error as e:
                self.logger.error(f"Error during retrieving a mediafile: " f"{repr(e)}")
                raise ServerError(f"Database error {e.pgcode}: {e.pgerror}")

    def _query(self, connection, file_id, file_type):
        with connection.cursor() as cur:
            if file_type == "mediafile":
                fetch_query = (
                    "SELECT data, mimetype FROM media.mediafile_data WHERE id=%s"
                )
            elif file_type == "resource":
                fetch_query = (
                    "SELECT data, mimetype FROM media.resource_data WHERE id=%s"
                )
            cur.execute(fetch_query, [file_id])
            row = cur.fetchone()
            if not row:
                raise NotFoundError(
                    f"The {file_type} with id {file_id} could not be found."
                )
            return (row[0], row[1])

    def set_mediafile(self, file_id, file_type, media, mimetype):
        while True:
            try:
                connection = self.get_connection()
                with connection:
                    self._insert(connection, file_id, file_type, media, mimetype)
                break
            except psycopg2.InterfaceError:
                if self.connection:
                    self.connection.close()
                self.connection = None
                self.logger.info("Database connection has been reset. Reconnect...")
            except psycopg2.Error as e:
                self.logger.error(f"Error during inserting a mediafile: {repr(e)}")
                raise ServerError(f"Database error {e.pgcode}: {e.pgerror}")

    def _insert(self, connection, file_id, file_type, media, mimetype):
        if file_type == "mediafile":
            insert_sql = (
                "INSERT INTO media.mediafile_data (id, data, mimetype) "
                " VALUES (%s, %s, %s)"
            )
        elif file_type == "resource":
            insert_sql = (
                "INSERT INTO media.resource_data (id, data, mimetype) "
                " VALUES (%s, %s, %s)"
            )

        with connection.cursor() as cur:
            cur.execute(
                insert_sql,
                (file_id, media, mimetype),
            )

    def get_connection(self):
        if not self.connection:
            self.connection = self.create_connection()
        return self.connection

    def create_connection(self):
        try:
            return psycopg2.connect(
                host=self.config["MEDIA_DATABASE_HOST"],
                port=self.config["MEDIA_DATABASE_PORT"],
                database=self.config["MEDIA_DATABASE_NAME"],
                user=self.config["MEDIA_DATABASE_USER"],
                password=self.config["MEDIA_DATABASE_PASSWORD"],
            )
        except psycopg2.Error as e:
            self.logger.error(f"Error during connect to the database: " f"{repr(e)}")
            raise ServerError(f"Database connect error {e.pgcode}: " f"{e.pgerror}")

    def shutdown(self):
        if self.connection:
            self.connection.close()
