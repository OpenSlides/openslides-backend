from typing import Any

from psycopg import Connection, rows, sql
from psycopg.errors import UndefinedColumn, UndefinedFunction, UndefinedTable

from openslides_backend.services.postgresql.db_connection_handling import (
    retry_on_db_failure,
)
from openslides_backend.shared.exceptions import DatabaseException, InvalidFormat
from openslides_backend.shared.filters import And, Filter, Not, Or
from openslides_backend.shared.patterns import Collection, Id
from openslides_backend.shared.typing import LockResult, Model, PartialModel

from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ..database.commands import GetManyRequest
from .mapped_fields import MappedFields
from .query_helper import SqlArguments, SqlQueryHelper

SqlArgumentsExtended = tuple[list[Id]] | SqlArguments


class DatabaseReader(SqlQueryHelper):

    def __init__(
        self, connection: Connection[rows.DictRow], logging: LoggingModule, env: Env
    ) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.connection = connection

    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        lock_result: LockResult = True,
    ) -> dict[Collection, dict[Id, PartialModel]]:
        """
        Returns the models requested in the shape of their requested fields.
        Will combine overlapping requests on the same id.
        Always adds the id to the fields.
        """
        result: dict[Collection, dict[Id, PartialModel]] = {
            get_many_request.collection: dict()
            for get_many_request in get_many_requests
        }

        for get_many_request in get_many_requests:
            if not (collection := get_many_request.collection):
                raise DatabaseException(
                    "No collection supplied. Give at least one collection."
                )
            if not (ids := get_many_request.ids):
                continue
            for id_ in ids:
                if not id_ > 0:
                    raise InvalidFormat("Id must be positive.")
            if get_many_request.mapped_fields is None:
                mapped_fields = MappedFields()
            else:
                mapped_fields = MappedFields(list(get_many_request.mapped_fields))
            if "id" not in mapped_fields.unique_fields:
                mapped_fields.unique_fields.append("id")

            mapped_fields_sql = self.build_select_from_mapped_fields(mapped_fields)
            query = sql.SQL(
                """SELECT {columns} FROM {view} WHERE id = ANY(%s)"""
            ).format(
                columns=mapped_fields_sql,
                view=sql.Identifier(collection),
            )
            db_result = self.execute_query(
                collection, query, lock_result, mapped_fields, (ids,)
            )
            self.insert_models_into_result(db_result, mapped_fields, result[collection])
            # result[collection].update(self.build_models_from_result(db_result, mapped_fields, collection))
        return result

    def get_all(
        self,
        collection: Collection,
        mapped_fields: MappedFields | None = None,
        lock_result: bool = True,
    ) -> dict[Id, PartialModel]:
        if mapped_fields is None:
            mapped_fields = MappedFields()
        mapped_fields_sql = self.build_select_from_mapped_fields(mapped_fields)
        query = sql.SQL("""SELECT {columns} FROM {collection}""").format(
            columns=mapped_fields_sql,
            collection=sql.Identifier(collection),
        )
        result: dict[Id, PartialModel] = dict()
        self.insert_models_into_result(
            self.execute_query(collection, query, lock_result, mapped_fields),
            mapped_fields,
            result,
        )
        return result

    def filter(
        self,
        collection: Collection,
        filter_: Filter,
        mapped_fields: MappedFields,
        lock_result: bool,
    ) -> dict[Id, Model]:
        query, arguments = self.build_filter_query(collection, filter_, mapped_fields)
        try:
            return self.fetch_models(
                collection, query, arguments, mapped_fields, lock_result
            )
        except InvalidFormat as e:
            if '"' in e.message:
                part_one, field, *_ = e.message.split('"')
                if "Field" in part_one and self.is_field_in_filter(field, filter_):
                    e.message += "\nCheck filter fields."
            raise e

    def is_field_in_filter(self, field: str, filter_: Filter) -> bool:
        if isinstance(filter_, Not):
            return self.is_field_in_filter(field, filter_.not_filter)
        elif isinstance(filter_, Or):
            return any(
                self.is_field_in_filter(field, part) for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return any(
                self.is_field_in_filter(field, part) for part in filter_.and_filter
            )
        else:
            return filter_.field == field

    def aggregate(
        self,
        collection: Collection,
        filter: Filter | None,
        agg_function: str,
        field_or_star: str,
        lock_result: bool,
    ) -> Any:
        """
        This function creates and executes an SQL query with an aggregate function like count or max.
        field_or_star should be "*" if count is used else the field to be aggregated on.
        Returns only the aggregate.
        """
        aggregate_function = sql.SQL("{aggregate_function}({agg_field})").format(
            agg_field=(
                sql.Identifier(field_or_star)
                if field_or_star != "*"
                else sql.Literal("*")
            ),
            aggregate_function=sql.SQL(agg_function),
        )
        query, arguments = self.build_filter_query(
            collection, filter, None, aggregate_function
        )
        return self.execute_query(
            collection, query, lock_result, None, arguments, aggregate=True
        )[0].get(agg_function)

    def fetch_models(
        self,
        collection: Collection,
        query: sql.Composed,
        arguments: SqlArgumentsExtended,
        mapped_fields: MappedFields,
        lock_result: bool,
    ) -> dict[int, Model]:
        """Fetched models for one collection"""
        result = self.execute_query(
            collection, query, lock_result, mapped_fields, arguments
        )
        models = {}
        for row in result:
            # if there are mapped_fields, we already resolved them in the query and
            # can just use all fields.
            models[row["id"]] = row
            if (
                not mapped_fields.needs_whole_model
                and "id" not in mapped_fields.unique_fields
            ):
                del row["id"]
        return models

    def insert_models_into_result(
        self,
        db_result: list[PartialModel],
        mapped_fields: MappedFields,
        collection_result_part: dict[Id, PartialModel],
    ) -> None:
        """
        Composes the result so that exactly the required fields are returned.
        Normally this means no None values.
        Exception: the mapped fields require the whole model.
        """
        for row in db_result:
            id_ = row["id"]

            if not mapped_fields.needs_whole_model and mapped_fields.unique_fields:
                if not (model := collection_result_part.get(id_, dict())):
                    collection_result_part[id_] = model
                # TODO is this nec3essary or obsolete by what has to be done after applying changed models anyway?
                for field in mapped_fields.unique_fields:
                    if row[field] is not None:
                        model[field] = row.get(field, None)
            else:
                collection_result_part[id_] = row

    def get_current_migration_index(self) -> int:
        #        result = self.connection.query(
        #            "select min(migration_index), max(migration_index) from positions", []
        #        )
        #        min_migration_index = result[0]["min"] if result else None
        #        max_migration_index = result[0]["max"] if result else None
        #        if min_migration_index != max_migration_index:
        #            raise InvalidDatastoreState(
        #                "The datastore has inconsistent migration indices: "
        #                + f"Minimum is {min_migration_index}, maximum is {max_migration_index}."
        #            )
        return -1

    @retry_on_db_failure
    def execute_query(
        self,
        collection: Collection,
        query: sql.Composed,
        lock_result: LockResult,
        mapped_fields: MappedFields | None = None,
        arguments: SqlArgumentsExtended = [],
        aggregate: bool = False,
    ) -> list[PartialModel]:
        if lock_result and not aggregate:
            query += sql.SQL(" FOR UPDATE")
        try:
            with self.connection.cursor() as curs:
                results = curs.execute(query, arguments).fetchall()
        except UndefinedColumn as e:
            column = e.args[0].split('"')[1]
            error_msg = (
                f"Field '{column}' does not exist in collection '{collection}': {e}"
            )
            if mapped_fields and column in mapped_fields.unique_fields:
                error_msg += "\nCheck mapped fields."
            raise InvalidFormat(error_msg)
        except UndefinedTable as e:
            raise InvalidFormat(
                f"Collection '{collection}' does not exist in the database: {e}"
            )
        except UndefinedFunction as e:
            raise InvalidFormat(e.diag.message_primary or "")
        except Exception as e:
            raise DatabaseException(f"Unexpected error reading from database: {e}")

        return results
