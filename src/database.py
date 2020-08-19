import psycopg2

from .cache import LRUCache
from .exceptions import ServerError


class Database:
    def __init__(self, app):
        self.config = app.config
        self.logger = app.logger
        self.connection = None
        self.cache = LRUCache(self.logger, 20)

    def get_mediafile(self, media_id):
        if self.cache.has_media_id(media_id):
            return self.cache.get_media(media_id)
        while True:
            connection = self.get_connection()
            try:
                with connection:
                    media = self._query(connection, media_id)
                    self.cache.set_media(media_id, media)
                    return media
            except psycopg2.InterfaceError:
                if self.connection:
                    self.connection.close()
                self.connection = None
                self.logger.info("Database connection has been reset. " "Reconnect...")
            except psycopg2.Error as e:
                self.logger.error(f"Error during retrieving a mediafile: " f"{repr(e)}")
                raise ServerError(f"Database error {e.pgcode}: {e.pgerror}")

    def _query(self, connection, media_id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT data, mimetype FROM mediafile_data WHERE id=%s", [media_id]
            )
            row = cur.fetchone()
            if not row:
                raise ServerError(
                    f"The mediafile with id {media_id} could not be found."
                )
            return (row[0], row[1])

    def set_mediafile(self, media_id, media, mimetype):
        while True:
            try:
                connection = self.get_connection()
                with connection:
                    self._insert(connection, media_id, media, mimetype)
                break
            except psycopg2.InterfaceError:
                if self.connection:
                    self.connection.close()
                self.connection = None
                self.logger.info("Database connection has been reset. Reconnect...")
            except psycopg2.Error as e:
                self.logger.error(f"Error during inserting a mediafile: {repr(e)}")
                raise ServerError(f"Database error {e.pgcode}: {e.pgerror}")

    def _insert(self, connection, media_id, media, mimetype):
        with connection.cursor() as cur:
            cur.execute(
                "INSERT INTO mediafile_data (id, data, mimetype) "
                " VALUES (%s, %s, %s)",
                (media_id, media, mimetype),
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
