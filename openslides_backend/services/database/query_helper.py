
# from datastore.shared.services.read_database import (
#    AggregateFilterQueryFieldsParameters,
#    BaseFilterQueryFieldsParameters,
#    CountFilterQueryFieldsParameters,
#    MappedFieldsFilterQueryFieldsParameters,
# )
# from datastore.shared.util import (
#    KEYSEPARATOR,
#    And,
#    BadCodingError,
#    DeletedModelsBehaviour,
#    Filter,
#    FilterOperator,
#    InvalidFormat,
#    Not,
#    Or,
# )
from mapped_fields import MappedFields

# extend if neccessary. first is always the default (should be int)
# min/max functions support the following:
# "any numeric, string, date/time, network, or enum type, or arrays of these types"
VALID_AGGREGATE_CAST_TARGETS = ["int"]

VALID_AGGREGATE_FUNCTIONS = ["min", "max", "count"]


class SqlQueryHelper:
    def build_select_from_mapped_fields(
        self, mapped_fields: MappedFields
    ) -> tuple[str, list[str]]:
        if mapped_fields.needs_whole_model:
            # at least one collection needs all fields, so we just select data and
            # calculate the mapped_fields later
            return "data", []
        else:
            return (
                ", ".join(["data->%s AS {}"] * len(mapped_fields.unique_fields)),
                mapped_fields.unique_fields,
            )

    def build_filter_query(
        self,
        collection: str,
        #        filter: Filter,
        #        fields_params: Optional[BaseFilterQueryFieldsParameters] = None,
        select_fqid: bool = False,
    ) -> None:  # -> Tuple[str, List[str], List[str]]:
        return None

    #        arguments: List[str] = []
    #        sql_parameters: List[str] = []
    #        filter_str = self.build_filter_str(filter, arguments)
    #
    #        arguments = [collection + KEYSEPARATOR + "%"] + arguments
    #
    #        if isinstance(fields_params, MappedFieldsFilterQueryFieldsParameters):
    #            fields, mapped_field_args = self.build_select_from_mapped_fields(
    #                fields_params.mapped_fields
    #            )
    #            arguments = mapped_field_args + arguments
    #            sql_parameters = fields_params.mapped_fields.unique_fields
    #        else:
    #            if isinstance(fields_params, CountFilterQueryFieldsParameters):
    #                fields = "count(*)"
    #            elif isinstance(fields_params, AggregateFilterQueryFieldsParameters):
    #                if fields_params.function not in VALID_AGGREGATE_FUNCTIONS:
    #                    raise BadCodingError(
    #                        "Invalid aggregate function: %s" % fields_params.function
    #                    )
    #                if fields_params.type not in VALID_AGGREGATE_CAST_TARGETS:
    #                    raise BadCodingError("Invalid cast type: %s" % fields_params.type)
    #
    #                fields = f"{fields_params.function}((data->>%s)::{fields_params.type})"
    #                arguments = [fields_params.field] + arguments
    #            else:
    #                raise BadCodingError(
    #                    f"Invalid fields_params for build_filter_query: {fields_params}"
    #                )
    #            fields += f" AS {fields_params.function},\
    #                        (SELECT MAX(position) FROM positions) AS position"
    #
    #        if select_fqid:
    #            fields = f"fqid as __fqid__, {fields}"
    #
    #        query = f"select {fields} from models where fqid like %s and ({filter_str})"
    #        return (
    #            query,
    #            arguments,
    #            sql_parameters,
    #        )
    #
    def build_filter_str(
        #        self, filter: Filter, arguments: List[str], table_alias=""
        self,
        filter: str,
        arguments: list[str],
        table_alias="",
    ) -> str:
        return ""


#        if isinstance(filter, Not):
#            filter_str = self.build_filter_str(
#                filter.not_filter, arguments, table_alias
#            )
#            return f"NOT ({filter_str})"
#        elif isinstance(filter, Or):
#            return " OR ".join(
#                f"({self.build_filter_str(part, arguments, table_alias)})"
#                for part in filter.or_filter
#            )
#        elif isinstance(filter, And):
#            return " AND ".join(
#                f"({self.build_filter_str(part, arguments, table_alias)})"
#                for part in filter.and_filter
#            )
#        elif isinstance(filter, FilterOperator):
#            if table_alias:
#                table_alias += "."
#            if filter.value is None:
#                if filter.operator not in ("=", "!="):
#                    raise InvalidFormat("You can only compare to None with = or !=")
#                operator = filter.operator[::-1].replace("=", "IS").replace("!", " NOT")
#                condition = f"{table_alias}data->>%s {operator} NULL"
#                arguments += [filter.field]
#            else:
#                if filter.operator == "~=":
#                    condition = f"LOWER({table_alias}data->>%s) = LOWER(%s::text)"
#                elif filter.operator == "%=":
#                    condition = f"{table_alias}data->>%s ILIKE %s::text"
#                elif filter.operator in ("=", "!="):
#                    condition = f"{table_alias}data->>%s {filter.operator} %s::text"
#                else:
#                    condition = f"({table_alias}data->%s)::numeric {filter.operator} %s"
#                arguments += [filter.field, filter.value]
#            return condition
#        else:
#            raise BadCodingError("Invalid filter type")
