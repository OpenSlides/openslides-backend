from collections import defaultdict
from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent, RequestDeleteEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator
from .exceptions import MigrationException

class Migration(BaseModelMigration):
    """
    This migration edits out duplications that are left in the database from previous bugs.

    It throws an aggregate error listing everything it can't edit if that isn't possible.
    """

    error_unique_fields: dict[str, list[list[str]]] = {
        "committee": [["external_id"]],
        "group": [["meeting_id", "external_id"]],
        "meeting": [["external_id"]],
        "meeting_user": [["meeting_id", "user_id"]],
        "motion": [["meeting_id", "number"]],
        "option": [["content_object_id", "poll_id"]],
        "structure_level_list_of_speakers": [["meeting_id", "structure_level_id", "list_of_speakers_id"]],
        "user": [["username"], ["member_number"], ["saml_id"]]
    }
    add_count_unique_fields: dict[str, dict[str, list[str]]] = {
        "chat_group": {"name": ["meeting_id"]},
        "gender": {"name": []},
        "mediafile": {"title": ["parent_id", "owner_id"]},
        "motion_state": {"name": ["workflow_id"]},
        "projector_countdown": {"title": ["meeting_id"]},
        "structure_level": {"name": ["meeting_id"]},
        "mediafile": {"token": []}
    }
    # field keys not included in unique fields for append text
    merge_values_unique_fields: dict[str, dict[tuple[str, ...], list[str]]]= {
        "motion_comment": {("comment",): ["motion_id", "section_id"]},
        "personal_note": {("note", "star"): ["meeting_user_id", "content_object_id"]}
    }
    delete_higher_weights_unique_fields: dict[str, list[str]] = {
        "motion_editor": ["meeting_user_id", "motion_id"],
        "motion_working_group_speaker": ["meeting_user_id", "motion_id"],
        "motion_submitter": ["meeting_user_id", "motion_id"],
        "motion_supporter": ["meeting_user_id", "motion_id"]
    }
    target_migration_index = 81

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        collections = set([
            *self.error_unique_fields,
            *self.add_count_unique_fields,
            *self.merge_values_unique_fields,
            *self.delete_higher_weights_unique_fields
        ])
        collection_to_fields: dict[str,list[str]]= {collection: list(set([
            *[field for fields in self.error_unique_fields.get(collection, []) for field in fields],
            *self.add_count_unique_fields.get(collection, {}),
            *[field for fields in self.add_count_unique_fields.get(collection, {}).values() for field in fields],
            *[field for fields in self.merge_values_unique_fields.get(collection, {}).keys() for field in fields],
            *[field for fields in self.merge_values_unique_fields.get(collection, {}).values() for field in fields],
            *([*fields, "weight", "id"] if (fields:=self.delete_higher_weights_unique_fields.get(collection, [])) else [])
        ])) for collection in collections}
        collection_to_tuples: dict[str, list[tuple[str, ...]]]= {collection: [
            *[tuple(fields) for fields in self.error_unique_fields.get(collection, [])],
            *[(change_field, *other_fields) for change_field, other_fields in self.add_count_unique_fields.get(collection, {}).items()],
            *[tuple(fields) for fields in self.merge_values_unique_fields.get(collection, {}).values()],
            *([tuple(fields)] if (fields:=self.delete_higher_weights_unique_fields.get(collection, [])) else [])
        ] for collection in collections}
        errors: list[str] = []
        events: list[BaseRequestEvent] = []
        for collection, fields in collection_to_fields.items():
            unique_tuple_to_data: dict[tuple[str, ...], dict[tuple[str, ...], list[int]]] = {
                tup: defaultdict(list) for tup in collection_to_tuples[collection]
            }
            unique_tuple_to_combinations_with_duplicates: dict[tuple[str, ...], list[tuple[str,...]]] = defaultdict(list)
            models = self.reader.get_all(collection, fields)
            for id_, model in models:
                for tup in collection_to_tuples[collection]:
                    vals = tuple(model[field] for field in tup)
                    if any(val is None for val in vals):
                        continue
                    unique_tuple_to_data[tup][vals].append(id_)
                    if len(unique_tuple_to_data[tup][vals])>1:
                        unique_tuple_to_combinations_with_duplicates[tup].append(vals)
            for fields in self.error_unique_fields.get(collection, []):
                tup = tuple(fields)
                for vals in unique_tuple_to_combinations_with_duplicates[tup]:
                    errors.append(f"{collection}: Ids {unique_tuple_to_data[tup][vals]}: Duplicate values for {tup} (values: {vals}) cannot be handled.")
            if len(errors):
                continue
            all_exchanged: list[str]= []
            for change_field, other_fields in self.add_count_unique_fields.get(collection, {}).items():
                tup = (change_field, *other_fields)
                for vals in unique_tuple_to_combinations_with_duplicates[tup]:
                    ids = sorted(unique_tuple_to_data[tup][vals])
                    i = 2
                    exchange: list[str] = []
                    while len(exchange) < len(ids[1:]):
                        check = vals[0] + f" ({i})"
                        if exchange not in all_exchanged and not self.datastore.filter(collection, FilterOperator(change_field, "=", check), ["id"]):
                            exchange.append(check)
                        i += 1
                    events.extend(
                        RequestUpdateEvent(fqid_from_collection_and_id(collection, id_), fields={tup[0]: exchange[i]}) for i, id_ in enumerate(ids[1:],)
                    )
                    print(f"{collection}: Updating ids {ids}: Duplicate values for {tup} (values: {vals}): Appending numbers to {change_field}...")
            for merge_fields, tup_fields in self.merge_values_unique_fields.get(collection, {}):
                tup = tuple(tup_fields)
                for vals in unique_tuple_to_combinations_with_duplicates[tup]:
                    ids = sorted(unique_tuple_to_data[tup][vals])
                    data = {}
                    for field in merge_fields:
                        field_vals = [val for id_ in ids if (val:= models[id_].get(field)) is not None]
                        if len(field_vals) == 1:
                            data[field] = field_vals[0]
                        elif len(field_vals) > 1:
                            if isinstance(field_vals[0], bool):
                                data[field] = any(field_vals)
                            else:
                                data[field] = "\n".join(field_vals)
                    if data:
                        events.append(RequestUpdateEvent(fqid_from_collection_and_id(collection, ids[0]), fields=data))
                    events.extend([
                        RequestDeleteEvent(fqid_from_collection_and_id(collection, id_)) for id_ in ids[1:]
                    ])
                    # TODO: Back relations?
                    print(f"{collection}: Ids {ids}: Duplicate values for {tup} (values: {vals}): Merging all into id {ids[0]}...")
            for fields in self.delete_higher_weights_unique_fields.get(collection, {}):
                tup = tuple(fields)
                for vals in unique_tuple_to_combinations_with_duplicates[tup]:
                    ids = sorted(unique_tuple_to_data[tup][vals])
                    broken_models = sorted([models[id_] for id_ in ids], key=lambda model: model.get("weight", 9999999))
                    events.extend([
                        RequestDeleteEvent(fqid_from_collection_and_id(collection, model["id"])) for model in broken_models[1:]
                    ])
                    # TODO: Back relations?
                    print(f"{collection}: Ids {ids}: Duplicate values for {tup} (values: {vals}): Deleting ids {[model['id'] for model in broken_models[1:]]}...")
        if len(errors):
            raise MigrationException(errors)
        return events