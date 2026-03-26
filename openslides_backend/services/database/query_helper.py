from psycopg import sql

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import Field
from openslides_backend.shared.exceptions import BadCodingException, InvalidFormat
from openslides_backend.shared.filters import And, Filter, FilterOperator, Not, Or

from .mapped_fields import MappedFields

SqlArguments = list[str | int]


# TODO move insert and select creation into this class?
class SqlQueryHelper:
    def build_select_from_mapped_fields(
        self, mapped_fields: MappedFields
    ) -> sql.Composed:
        """
        Returns an sql.Composed string:
        - of the mapped fields
        - or of all the fields if any of them must be fetched with a custom sql
        Returns only * otherwise.
        """
        unique_fields = (
            [] if mapped_fields.needs_whole_model else mapped_fields.unique_fields
        )
        enum_array_sql = {}

        def create_sql_for_enum_array(collection: str, field: str) -> sql.Composed:
            return sql.Composed(
                [
                    sql.SQL("array(SELECT unnest("),
                    sql.Identifier(collection),
                    sql.SQL("."),
                    sql.Identifier(field),
                    sql.SQL(f")::text) AS {field}"),
                ]
            )

        if collection := mapped_fields.collection:
            model = model_registry.get(collection)
            if model:
                enum_array_sql = {
                    field.get_own_field_name(): create_sql_for_enum_array(
                        collection, field.get_own_field_name()
                    )
                    for field in model().get_enum_array_fields()
                }
                if enum_array_sql and not unique_fields:
                    unique_fields = [
                        val.get_own_field_name() for val in model().get_fields()
                    ]

        if not unique_fields:
            return sql.SQL("*")  # type: ignore
        else:
            return sql.SQL(", ").join(
                [
                    enum_array_sql.get(field) or sql.Identifier(field)
                    for field in {*unique_fields, "id"}
                ]
            )

    def build_filter_query(
        self,
        collection: str,
        filter_: Filter | None,
        mapped_fields: MappedFields | None,
        aggregate_function: sql.Composed | None = None,
    ) -> tuple[sql.Composed, SqlArguments]:
        """
        returns in the returned tuple:
        * the query string
        * the arguments to be used within that query
        """
        arguments: SqlArguments = []

        if mapped_fields:
            mapped_fields.collection = collection
            aggregate_function = self.build_select_from_mapped_fields(mapped_fields)
        query = sql.SQL("SELECT {columns} FROM {view}").format(
            view=sql.Identifier(collection),
            columns=aggregate_function,
        )
        if filter_:
            query += sql.SQL(" WHERE ({filter_str})").format(
                filter_str=self.build_filter_str(filter_, arguments, collection)
            )
        return (
            query,
            arguments,
        )

    def build_filter_str(
        self,
        filter_: Filter,
        arguments: SqlArguments,
        collection: str,
        table_alias: str = "",
    ) -> sql.Composed | sql.Identifier:
        """
        appends the values to the arguments list
        returns the filter string
        """
        if isinstance(filter_, Not):
            return sql.SQL("NOT ({filter_str})").format(
                filter_str=self.build_filter_str(
                    filter_.not_filter, arguments, collection, table_alias
                )
            )
        elif isinstance(filter_, Or):
            return sql.SQL(" OR ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=self.build_filter_str(
                        part, arguments, collection, table_alias
                    )
                )
                for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return sql.SQL(" AND ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=self.build_filter_str(
                        part, arguments, collection, table_alias
                    )
                )
                for part in filter_.and_filter
            )
        elif isinstance(filter_, FilterOperator):
            if table_alias:
                table_column: sql.Composed | sql.Identifier = sql.SQL(
                    "{table_alias}.{column_name}"
                ).format(
                    table_alias=sql.Identifier(table_alias),
                    column_name=sql.Identifier(filter_.field),
                )
            else:
                table_column = sql.Identifier(filter_.field)
            if filter_.value is None:
                if filter_.operator not in ("=", "!="):
                    raise InvalidFormat("You can only compare to None with = or !=")
                operator = (
                    filter_.operator[::-1].replace("=", "IS").replace("!", " NOT")
                )
                condition = sql.SQL("{table_column} {operator} NULL").format(
                    table_column=table_column, operator=sql.SQL(operator)
                )
            else:
                if filter_.operator == "~=":
                    condition = sql.SQL(
                        "LOWER({table_column}) = LOWER(%s::text)"
                    ).format(table_column=table_column)
                elif filter_.operator == "%=":
                    condition = sql.SQL("{table_column} ILIKE %s::text").format(
                        table_column=table_column
                    )
                elif filter_.operator == "in":
                    condition = sql.SQL("{table_column} = ANY(%s)").format(
                        table_column=table_column
                    )
                elif filter_.operator == "has":
                    condition = sql.SQL("%s = ANY({table_column})").format(
                        table_column=table_column
                    )
                # TODO delete or use if all backend tests were run.
                # elif filter_.operator in ("=", "!=") and isinstance(filter_.value, str):
                #     condition = sql.SQL("{table_column} {filter_operator} %s::text").format(
                #         table_column=table_column, filter_operator=sql.SQL(filter_.operator)
                #     )
                elif filter_.operator in ("=", "!=") and isinstance(
                    filter_.value, list
                ):
                    field = model_registry[collection]().get_field(filter_.field)
                    condition = sql.SQL(
                        "{table_column} {filter_operator} %s{type}"
                    ).format(
                        table_column=table_column,
                        filter_operator=sql.SQL(filter_.operator),
                        type=self.get_array_type(
                            field,
                            (type(next(iter(filter_.value))) if filter_.value else int),
                        ),
                    )
                else:
                    condition = sql.SQL("{table_column} {filter_operator} %s").format(
                        table_column=table_column,
                        filter_operator=sql.SQL(filter_.operator),
                    )
                arguments += [filter_.value]
            return condition
        else:
            raise BadCodingException("Invalid filter type")

    def get_array_type(self, field: Field, list_type: type) -> sql.Composable:
        if list_type == int:
            return sql.SQL("::integer[]")
        if enum_name := getattr(field, "enum_name", None):
            return sql.SQL(f"::{enum_name}")
        if list_type == str:
            return sql.SQL("::text[]")
        raise ValueError("Only integer or string lists are supported.")
