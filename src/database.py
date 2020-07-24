import psycopg2

from .cache import NullCache
from .exceptions import ServerError


class Database:
    def __init__(self, app):
        self.config = app.config
        self.logger = app.logger
        self.connection = None
        self.cache = NullCache(self.logger)

    def get_mediafile(self, media_id):
        if self.cache.has_media_id(media_id):
            return self.cache.get_media(media_id)
        while True:
            connection = self.get_connection()
            try:
                media = self._query(connection, media_id)
                self.cache.set_media(media_id, media)
                return media
            except psycopg2.InterfaceError:
                if self.connection:
                    self.connection.close()
                self.connection = None
                self.logger.info(
                    "Database connection has been reset. Reconnect...")
            except psycopg2.Error as e:
                self.logger.error(
                    f"Error during retrieving a mediafile: {repr(e)}")
                raise ServerError(f"Database error {e.pgcode}: {e.pgerror}")

    def _query(self, connection, media_id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT data, mimetype FROM mediafile_data WHERE id=%s",
                [media_id])
            row = cur.fetchone()
            if not row:
                raise ServerError(
                    f"The mediafile with id {media_id} could not be found.")
            return (row[0], row[1])

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
            self.logger.error(
                f"Error during connect to the database: {repr(e)}")
            raise ServerError(
                f"Database connect error {e.pgcode}: {e.pgerror}")

    def shutdown(self):
        if self.connection:
            self.connection.close()
