from typing import Protocol

from openslides_backend.datastore.shared.di import service_interface


class DatabaseError(Exception):
    def __init__(self, msg, base_exception: Exception | None = None):
        self.msg = msg
        self.base_exception = base_exception


@service_interface
class ConnectionHandler(Protocol):
    def get_connection_context(self):
        """Returns the connection"""

    def to_json(self, data):
        """
        Converts the dict/list/string/int to the database
        specific json representation
        """

    def execute(self, query, arguments, sql_parameters=[], use_execute_values=False):
        """Executes the query."""

    def query(self, query, arguments, sql_parameters=[], use_execute_values=False):
        """
        Executes the query. returns all results in a matrix-fashion:
        Each row is a result, and each column one value of one result.
        The columns are given as defined in the query.
        """

    def query_single_value(self, query, arguments, sql_parameters=[]):
        """
        This will return None, if no row was returned.
        Otherwise it will expect the row to have exactly
        one entry. This one is returned. Note, that you
        cannot distinguish between no returned row and one
        row, that contains null.
        """

    def query_list_of_single_values(
        self, query, arguments, sql_parameters=[], use_execute_values=False
    ):
        """
        Returns a list of values of each row. It is expected that each
        row returns exactly one value. An empty list will be returned if
        no rows were returned from the db.
        """
