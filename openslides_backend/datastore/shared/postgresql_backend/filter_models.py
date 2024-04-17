import re
from copy import deepcopy
from typing import Any

from openslides_backend.shared.filters import Filter
from openslides_backend.shared.patterns import (
    Collection,
    FullQualifiedId,
    collection_from_fqid,
)
from openslides_backend.shared.typing import Model

from .sql_query_helper import SqlQueryHelper

MODEL_FIELD_SQL = "data->>%s"
MODEL_FIELD_NUMERIC_SQL = r"\(data->%s\)::numeric"
MODEL_FIELD_NUMERIC_REPLACE = "(data->%s)::numeric"
COMPARISON_VALUE_TEXT_SQL = "%s::text"
COMPARISON_VALUE_SQL = "%s"


def is_comparable(a: Any, b: Any) -> bool:
    """
    Check if one of a or b is a subclass of the other and that they have a comparable basic
    type.
    """
    return (isinstance(a, type(b)) or isinstance(b, type(a))) and isinstance(
        a, (int, float, str)
    )


def filter_models(
    models: dict[FullQualifiedId, Model],
    collection: Collection,
    filter: Filter,
    mapped_fields: list[str] | None = None,
) -> dict[int, dict[str, Any]]:
    """
    Uses the SqlQueryHelper to build an SQL query for the given filter, transforms it into valid
    python code and then executes it to filter models in-memory.
    """
    # Build sql query for this filter. The arguments array contains the replacements for all %s in the query in the
    # correct order.
    query_helper = SqlQueryHelper()
    arguments: list[str] = []
    sql_query = query_helper.build_filter_str(filter, arguments)

    # transform query into valid python code
    filter_code = sql_query.lower().replace("null", "None").replace(" = ", " == ")
    # regex for all FilterOperators which were translated by the SqlQueryHelper
    regex = (
        rf"(?:{MODEL_FIELD_SQL}|lower\({MODEL_FIELD_SQL}\)|"
        rf"{MODEL_FIELD_NUMERIC_SQL}|lower\({MODEL_FIELD_NUMERIC_SQL}\))"
        r" (<|<=|>=|>|==|!=|is|is not|ilike) "
        rf"({COMPARISON_VALUE_SQL}|lower\({COMPARISON_VALUE_SQL}\)|"
        rf"{COMPARISON_VALUE_TEXT_SQL}|lower\({COMPARISON_VALUE_TEXT_SQL}\)|None)"
    )
    matches = re.findall(regex, filter_code)
    # this will hold all items from arguments, but correctly formatted for python and enhanced with validity checks
    formatted_args = []
    i = 0
    for match in matches:
        # for these operators, ensure that the model field is actually comparable to prevent TypeErrors
        if match[0] in ("<", "<=", ">=", ">"):
            val_str = (
                arguments[i + 1]
                if isinstance(arguments[i + 1], (int, float))
                else repr(arguments[i + 1])
            )
            formatted_args.append(
                f'is_comparable(model.get("{arguments[i]}"), {val_str}) and model.get("{arguments[i]}")'
            )
        elif match[0] == "ilike":
            raise NotImplementedError("Operator %= is not supported")
        else:
            formatted_args.append(f'model.get("{arguments[i]}")')
        i += 1
        # if comparison happens with a value, append it as well
        if match[1] in (
            COMPARISON_VALUE_SQL,
            f"lower({COMPARISON_VALUE_SQL})",
            COMPARISON_VALUE_TEXT_SQL,
            f"lower({COMPARISON_VALUE_TEXT_SQL})",
        ):
            formatted_args.append(repr(arguments[i]))
            i += 1
    # replace SQL placeholders and SQL specific code with the formatted python snippets
    filter_code = (
        filter_code.replace(MODEL_FIELD_NUMERIC_REPLACE, "{}")
        .replace(COMPARISON_VALUE_TEXT_SQL, "{}")
        .replace(MODEL_FIELD_SQL, "{}")
        .replace(COMPARISON_VALUE_SQL, "{}")
    )
    filter_code = filter_code.format(*formatted_args)

    # needed for generated code since postgres uses it
    def lower(s: str) -> str:
        return s.lower()

    # run eval with the generated code
    scope = locals()
    # copy globals we need explicitly to avoid copying all globals
    scope["collection_from_fqid"] = collection_from_fqid
    scope["is_comparable"] = is_comparable
    results = {
        model["id"]: (
            {field: model[field] for field in mapped_fields if field in model}
            if mapped_fields
            else model
        )
        for fqid, model in models.items()
        if collection_from_fqid(fqid) == collection
        and eval(filter_code, scope, locals())
    }
    return deepcopy(results)
