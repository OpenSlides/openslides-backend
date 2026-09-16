from psycopg import sql

from openslides_backend.models.base import model_registry
from openslides_backend.shared.filters import BaseSqlQueryHelper, Filter, SqlArguments

from .mapped_fields import MappedFields


# TODO move insert and select creation into this class?
class SqlQueryHelper(BaseSqlQueryHelper):
    def build_select_from_mapped_fields(
        self, mapped_fields: MappedFields
    ) -> sql.Composed:
        """
        Returns an sql.Composed string:
        - of the mapped fields if mapped fields are provided
        - of all the fields explicitly if any of them must be fetched with a custom sql and the whole model is required
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

    @staticmethod
    def get_enum_array_name(collection: str, field_name: str) -> str | None:
        field = model_registry[collection]().get_field(field_name)
        return getattr(field, "enum_name", None)
