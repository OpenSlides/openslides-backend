from typing import Any, cast

from datastore.migrations import BaseModelMigration
from datastore.reader.core import GetManyRequestPart
from datastore.writer.core.write_request import BaseRequestEvent

from openslides_backend.models.base import model_registry
from openslides_backend.models.fields import (
    BaseRelationField,
    GenericRelationField,
    GenericRelationListField,
)
from openslides_backend.shared.patterns import collection_and_id_from_fqid

from ...shared.filters import And, FilterOperator
from ..exceptions import MigrationException

# main_coll, main_field, back_coll, back_field -> sorted_equal_fields, main_field_def, back_field_def
Relations = dict[
    tuple[tuple[str, str], tuple[str, str]],
    tuple[tuple[str, ...], dict[str, Any], dict[str, Any]],
]


class Migration(BaseModelMigration):
    """
    This migration reads the meta models.yml and checks the integrity of all equal_fields.

    It throws an aggregate error listing everything that is broken.
    """

    target_migration_index = 82

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        self.load_models()
        relations = self.get_relations()
        errors: set[str] = set()
        for ((collection1, field1), (collection2, field2)), (
            eq_fields,
            field_def1,
            field_def2,
        ) in relations.items():
            affected_models1, affected_models2 = self.get_affected_models(
                collection1,
                field1,
                field_def1,
                collection2,
                field2,
                field_def2,
                eq_fields,
            )
            matches = self.find_matches(
                collection1,
                field1,
                field_def1,
                affected_models1,
                collection2,
                field2,
                field_def2,
                affected_models2,
            )
            for match in matches:
                if error := self.check_equal_data(
                    match,
                    collection1,
                    field1,
                    affected_models1,
                    collection2,
                    field2,
                    affected_models2,
                    eq_fields,
                ):
                    errors.add(error)
        if len(errors):
            raise MigrationException(list(errors))
        return None

    def load_models(self) -> None:
        self.models: dict[str, dict[str, dict[str, Any]]] = {
            collection: {
                field.own_field_name: (
                    {
                        "to": cast(BaseRelationField, field).to,
                        "equal_fields": cast(BaseRelationField, field).equal_fields,
                        "is_relation": True,
                        "is_generic": isinstance(field, GenericRelationField)
                        or isinstance(field, GenericRelationListField),
                        "is_list_relation": cast(
                            BaseRelationField, field
                        ).is_list_field,
                    }
                    if hasattr(field, "to")
                    else {
                        "is_relation": False,
                        "is_generic": False,
                        "is_list_relation": False,
                    }
                )
                for field in Model().get_fields()
            }
            for collection, Model in model_registry.items()
        }

    def get_relations(
        self,
    ) -> Relations:
        relations: Relations = {}

        for collection, fields in self.models.items():
            for field, field_def in fields.items():
                if eq := set(field_def.get("equal_fields", [])):
                    back_data = self.get_relation_data(field_def)
                    for back_collection, back_field_data in back_data.items():
                        for back_field, back_field_def in back_field_data.items():
                            if (
                                full_eq := self.calculate_full_equal_fields(
                                    eq, back_field_def, [collection, back_collection]
                                )
                            ) and (
                                self.is_a_main_relation(
                                    collection,
                                    field,
                                    field_def,
                                    back_collection,
                                    back_field,
                                    back_field_def,
                                )
                                or not back_field_def.get("equal_fields")
                            ):
                                full_eq_tup = tuple(sorted(full_eq))
                                relations[
                                    (collection, field),
                                    (back_collection, back_field),
                                ] = (full_eq_tup, field_def, back_field_def)
        return relations

    def get_relation_data(
        self, field_def: dict[str, Any]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        if field_def["is_generic"]:
            return {
                coll: {back_field: self.models[coll][back_field]}
                for coll, back_field in field_def["to"].items()
            }
        back_collection, back_field = list(field_def["to"].items())[0]
        back_field_def = self.models[back_collection][back_field]
        return {back_collection: {back_field: back_field_def}}

    def calculate_full_equal_fields(
        self,
        front_equal_fields: set[str],
        back_field_def: dict[str, Any],
        collections: list[str] = [],
    ) -> set[str]:
        if back_eq := back_field_def.get("equal_fields"):
            full_eq = (
                {*front_equal_fields, back_eq}
                if isinstance(back_eq, str)
                else front_equal_fields.union(back_eq)
            )
        else:
            full_eq = front_equal_fields
        if "user" in collections and "meeting_id" in full_eq:
            # Removing user/meeting_id check because it's ignored post-relDB
            return full_eq.difference({"meeting_id"})
        return full_eq

    def is_a_main_relation(
        self,
        coll_a: str,
        field_a: str,
        field_def_a: dict[str, Any],
        coll_b: str,
        field_b: str,
        field_def_b: dict[str, Any],
    ) -> bool:
        if field_def_a["is_generic"] != (generic_b := field_def_b["is_generic"]):
            return generic_b
        if field_def_a["is_list_relation"] != (
            list_b := field_def_b["is_list_relation"]
        ):
            return list_b
        if coll_a == coll_b:
            return field_a <= field_b
        return coll_a < coll_b

    def get_affected_models(
        self,
        collection1: str,
        field1: str,
        field_def1: dict[str, Any],
        collection2: str,
        field2: str,
        field_def2: dict[str, Any],
        eq_fields: tuple[str, ...],
    ) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
        affected_models1 = self.get_initial_affected_models(
            collection1, field1, eq_fields
        )
        affected_models2 = self.get_initial_affected_models(
            collection2, field2, eq_fields
        )
        self.update_affected_models(
            collection1,
            field1,
            affected_models1,
            field2,
            field_def2,
            affected_models2,
            eq_fields,
        )
        self.update_affected_models(
            collection2,
            field2,
            affected_models2,
            field1,
            field_def1,
            affected_models1,
            eq_fields,
        )
        return affected_models1, affected_models2

    def get_initial_affected_models(
        self, collection: str, relation_field: str, eq_fields: tuple[str, ...]
    ) -> dict[int, dict[str, Any]]:
        return self.reader.filter(
            collection,
            And(
                FilterOperator(relation_field, "!=", None),
                FilterOperator("meta_deleted", "=", False),
            ),
            self.get_affected_models_load_fields(collection, relation_field, eq_fields),
        )

    def update_affected_models(
        self,
        collection1: str,
        relation_field1: str,
        affected_models1: dict[int, dict[str, Any]],
        relation_field2: str,
        field_def2: dict[str, Any],
        affected_models2: dict[int, dict[str, Any]],
        eq_fields: tuple[str, ...],
    ) -> None:
        if other_affected_model_ids1 := self.get_other_affected_model_ids(
            relation_field2, field_def2, affected_models2, collection1, affected_models1
        ):
            affected_models1.update(
                self.reader.get_many(
                    [
                        GetManyRequestPart(
                            collection1,
                            other_affected_model_ids1,
                            self.get_affected_models_load_fields(
                                collection1, relation_field1, eq_fields
                            ),
                        )
                    ]
                )[collection1]
            )

    def get_affected_models_load_fields(
        self, collection: str, field: str, eq_fields: tuple[str, ...]
    ) -> list[str]:
        return list(
            {
                field,
                *(
                    [f for f in eq_fields if f != "meeting_id"]
                    if collection == "meeting" and "meeting_id" in eq_fields
                    else eq_fields
                ),
            }
        )

    def get_other_affected_model_ids(
        self,
        field1: str,
        field_def1: dict[str, Any],
        affected_models1: dict[int, dict[str, Any]],
        collection2: str,
        affected_models2: dict[int, dict[str, Any]],
    ) -> list[int]:
        is_generic = field_def1["is_generic"]
        missing_ids: set[int] = set()
        for model in affected_models1.values():
            if field_def1["is_list_relation"]:
                for entry in model.get(field1) or []:
                    if is_generic:
                        coll2, id_ = collection_and_id_from_fqid(entry)
                        if coll2 != collection2:
                            continue
                    else:
                        id_ = entry
                    if id_ not in affected_models2:
                        missing_ids.add(id_)
            elif is_generic:
                if fqid := model.get(field1):
                    coll2, id_ = collection_and_id_from_fqid(fqid)
                    if coll2 == collection2 and id_ not in affected_models2:
                        missing_ids.add(id_)
            elif (id_val := (model.get(field1))) and id_val not in affected_models2:
                missing_ids.add(id_val)
        return sorted(missing_ids)

    def find_matches(
        self,
        collection1: str,
        field1: str,
        field_def1: dict[str, Any],
        affected_models1: dict[int, dict[str, Any]],
        collection2: str,
        field2: str,
        field_def2: dict[str, Any],
        affected_models2: dict[int, dict[str, Any]],
    ) -> set[tuple[int, int]]:
        return self.find_matches_helper(
            field1, field_def1, affected_models1, collection2
        ).union(
            self.find_matches_helper(
                field2, field_def2, affected_models2, collection1, reverse=True
            )
        )

    def find_matches_helper(
        self,
        field: str,
        field_def: dict[str, Any],
        affected_models: dict[int, dict[str, Any]],
        other_collection: str,
        reverse: bool = False,
    ) -> set[tuple[int, int]]:
        matches: set[tuple[int, int]] = set()
        for model_id, model in affected_models.items():
            if field_def["is_list_relation"]:
                for element in model.get(field) or []:
                    if field_def["is_generic"]:
                        coll, id_ = collection_and_id_from_fqid(element)
                        if coll == other_collection:
                            matches.add((id_, model_id) if reverse else (model_id, id_))
                    else:
                        matches.add(
                            (element, model_id) if reverse else (model_id, element)
                        )
            elif element := model.get(field):
                if field_def["is_generic"]:
                    coll, id_ = collection_and_id_from_fqid(element)
                    if coll == other_collection:
                        matches.add((id_, model_id) if reverse else (model_id, id_))
                else:
                    matches.add((element, model_id) if reverse else (model_id, element))
        return matches

    def check_equal_data(
        self,
        match: tuple[int, int],
        collection1: str,
        field1: str,
        affected_models1: dict[int, dict[str, Any]],
        collection2: str,
        field2: str,
        affected_models2: dict[int, dict[str, Any]],
        equal_fields: tuple[str, ...],
    ) -> str | None:
        """
        Checks equal_data between two entries.
        Returns an error-string if there is a difference
        """
        id1, id2 = match
        eq_data_tup1 = self.get_equal_data_tuple(
            collection1, id1, affected_models1, equal_fields
        )
        eq_data_tup2 = self.get_equal_data_tuple(
            collection2, id2, affected_models2, equal_fields
        )
        if eq_data_tup1 != eq_data_tup2:
            the_problem = " and ".join(
                sorted(
                    [
                        f"{collection1}/{id1}/{field1}: {eq_data_tup1}",
                        f"{collection2}/{id2}/{field2}: {eq_data_tup2}",
                    ]
                )
            )
            return f"Detected different equal_fields: {the_problem} for equal_fields {equal_fields}"
        return None

    def get_equal_data_tuple(
        self,
        collection: str,
        id_: int,
        affected_models: dict[int, dict[str, Any]],
        sorted_eqfs: tuple[str, ...],
    ) -> tuple[Any, ...]:
        model = affected_models.get(id_, {})
        return tuple(
            [
                (
                    id_
                    if collection == "meeting" and eq_field == "meeting_id"
                    else model.get(eq_field)
                )
                for eq_field in sorted_eqfs
            ]
        )
