from psycopg import sql

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
        returns an sql.Composed string of the mapped fields.
        returns only * if all fields are needed.
        """
        if mapped_fields.needs_whole_model:
            # at least one collection needs all fields, so we just select data and
            # calculate the mapped_fields later
            return sql.SQL("*")  # type: ignore
        else:
            result = sql.SQL(", ").join(
                sql.Identifier(field) for field in {*mapped_fields.unique_fields, "id"}
            )
            return result

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
            aggregate_function = self.build_select_from_mapped_fields(mapped_fields)
        query = sql.SQL("SELECT {columns} FROM {view}").format(
            view=sql.Identifier(collection),
            columns=aggregate_function,
        )
        if filter_:
            query += sql.SQL(" WHERE ({filter_str})").format(
                filter_str=self.build_filter_str(filter_, arguments)
            )
        return (
            query,
            arguments,
        )

    def build_filter_str(
        self,
        filter_: Filter,
        arguments: SqlArguments,
        table_alias: str = "",
    ) -> sql.Composed | sql.Identifier:
        """
        appends the values to the arguments list
        returns the filter string
        """
        if isinstance(filter_, Not):
            return sql.SQL("NOT ({filter_str})").format(
                filter_str=self.build_filter_str(
                    filter_.not_filter, arguments, table_alias
                )
            )
        elif isinstance(filter_, Or):
            return sql.SQL(" OR ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=self.build_filter_str(part, arguments, table_alias)
                )
                for part in filter_.or_filter
            )
        elif isinstance(filter_, And):
            return sql.SQL(" AND ").join(
                sql.SQL("({filter_str})").format(
                    filter_str=self.build_filter_str(part, arguments, table_alias)
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
                # TODO delete or use if all backend tests were run.
                # elif filter_.operator in ("=", "!=") and isinstance(filter_.value, str):
                #     condition = sql.SQL("{table_column} {filter_operator} %s::text").format(
                #         table_column=table_column, filter_operator=sql.SQL(filter_.operator)
                #     )
                elif filter_.operator in ("=", "!=") and isinstance(
                    filter_.value, list
                ):
                    first_elem = next(iter(filter_.value))
                    condition = sql.SQL(
                        "{table_column} {filter_operator} %s::{type}"
                    ).format(
                        table_column=table_column,
                        filter_operator=sql.SQL(filter_.operator),
                        type=sql.SQL(
                            "text[]" if isinstance(first_elem, str) else "integer[]"
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
