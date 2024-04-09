from typing import Union

from openslides_backend.datastore.shared.typing import Field, Model

ListUpdatesDict = dict[Field, list[Union[str, int]]]


def apply_fields(
    model: Model,
    add: ListUpdatesDict,
    remove: ListUpdatesDict,
) -> Model:
    modified_fields = {}
    for field, value in add.items():
        # Iterate over list and remove all entries from value which are already
        # in the list. If adding multiple entries, this reduces the runtime needed.
        # When a huge amount of data is added, the normal update should be used
        # instead.
        db_list = model.get(field, [])
        db_list = db_list + [el for el in value if el not in db_list]  # type: ignore
        modified_fields[field] = db_list

    for field, value in remove.items():
        if field not in model:
            continue

        if field in modified_fields:
            db_list = modified_fields[field]
        else:
            db_list = model[field]
        modified_fields[field] = [el for el in db_list if el not in value]  # type: ignore

    return modified_fields
