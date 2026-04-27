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


class Migration(BaseModelMigration):
    """
    This migration reads the meta models.yml and checks the integrity of all equal_fields.

    It throws an aggregate error listing everything that is broken.
    """

    target_migration_index = 82

    def migrate_models(self) -> list[BaseRequestEvent] | None:
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
                field1, field_def1, affected_models1, collection2
            ).union(
                self.find_matches(
                    field2, field_def2, affected_models2, collection1, reverse=True
                )
            )
            sorted_eqfs = sorted(eq_fields)
            for id1, id2 in matches:
                model1 = affected_models1[id1]
                model2 = affected_models2[id2]
                eq_data1: list[Any] = []
                eq_data2: list[Any] = []
                for eq_field in sorted_eqfs:
                    eq_data1.append(model1.get(eq_field))
                    if collection2 == "meeting" and eq_field == "meeting_id":
                        eq_data2.append(id2)
                    else:
                        eq_data2.append(model2.get(eq_field))
                eq_data_tup1 = tuple(eq_data1)
                eq_data_tup2 = tuple(eq_data2)
                if eq_data_tup1 != eq_data_tup2:
                    the_problem = " and ".join(
                        sorted(
                            [
                                f"{collection1}/{id1}/{field1}: {eq_data_tup1}",
                                f"{collection2}/{id2}/{field2}: {eq_data_tup2}",
                            ]
                        )
                    )
                    errors.add(
                        f"Detected different equal_fields: {the_problem} for equal_fields {tuple(sorted_eqfs)}"
                    )
        if len(errors):
            raise MigrationException(list(errors))
        return None

    def find_matches(
        self,
        field: str,
        field_def: dict[str, Any],
        affected_models: dict[int, dict[str, Any]],
        other_collection: str,
        reverse: bool = False,
    ) -> set[tuple[int, int]]:
        matches: set[tuple[int, int]] = set()
        is_generic1, is_list1 = self.get_relation_flags(field_def)
        for model_id, model in affected_models.items():
            if is_list1:
                for element in model.get(field) or []:
                    if is_generic1:
                        coll, id_ = collection_and_id_from_fqid(element)
                        if coll == other_collection:
                            matches.add((id_, model_id) if reverse else (model_id, id_))
                    else:
                        matches.add(
                            (element, model_id) if reverse else (model_id, element)
                        )
            elif element := model.get(field):
                if is_generic1:
                    coll, id_ = collection_and_id_from_fqid(element)
                    if coll == other_collection:
                        matches.add((id_, model_id) if reverse else (model_id, id_))
                else:
                    matches.add((element, model_id) if reverse else (model_id, element))
        return matches

    def get_relation_flags(self, field_def: dict[str, Any]) -> tuple[bool, bool]:
        return field_def["is_generic"], field_def["is_list_relation"]

    def get_affected_models(
        self,
        collection1: str,
        field1: str,
        field_def1: dict[str, Any],
        collection2: str,
        field2: str,
        field_def2: dict[str, Any],
        eq_fields: set[str],
    ) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
        affected_models1 = self.reader.filter(
            collection1,
            And(
                FilterOperator(field1, "!=", None),
                FilterOperator("meta_deleted", "=", False),
            ),
            list({field1, *eq_fields}),
        )
        if collection2 == "meeting" and "meeting_id" in eq_fields:
            affected_models2 = self.reader.filter(
                collection2,
                And(
                    FilterOperator(field2, "!=", None),
                    FilterOperator("meta_deleted", "=", False),
                ),
                list({field2, *[f for f in eq_fields if f != "meeting_id"]}),
            )
        else:
            affected_models2 = self.reader.filter(
                collection2,
                And(
                    FilterOperator(field2, "!=", None),
                    FilterOperator("meta_deleted", "=", False),
                ),
                list({field2, *eq_fields}),
            )
        if other_affected_model_ids1 := self.get_other_affected_model_ids(
            field2, field_def2, affected_models2, collection1, affected_models1
        ):
            affected_models1.update(
                self.reader.get_many(
                    [
                        GetManyRequestPart(
                            collection1,
                            other_affected_model_ids1,
                            list({field1, *eq_fields}),
                        )
                    ]
                )[collection1]
            )
        if other_affected_model_ids2 := self.get_other_affected_model_ids(
            field1, field_def1, affected_models1, collection2, affected_models2
        ):
            if collection2 == "meeting" and "meeting_id" in eq_fields:
                affected_models2.update(
                    self.reader.get_many(
                        [
                            GetManyRequestPart(
                                collection2,
                                other_affected_model_ids2,
                                list(
                                    {
                                        field2,
                                        *[f for f in eq_fields if f != "meeting_id"],
                                    }
                                ),
                            )
                        ]
                    )[collection2]
                )
            else:
                affected_models2.update(
                    self.reader.get_many(
                        [
                            GetManyRequestPart(
                                collection2,
                                other_affected_model_ids2,
                                list({field2, *eq_fields}),
                            )
                        ]
                    )[collection2]
                )
        return affected_models1, affected_models2

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
                        coll, id_ = collection_and_id_from_fqid(entry)
                        if coll != collection2:
                            continue
                    else:
                        id_ = entry
                    if id_ not in affected_models2:
                        missing_ids.add(id_)
            elif is_generic:
                if fqid := model.get(field1):
                    coll, id_ = collection_and_id_from_fqid(fqid)
                    if coll == collection2 and id_ not in affected_models2:
                        missing_ids.add(id_)
            elif (id_val := (model.get(field1))) and id_val not in affected_models2:
                missing_ids.add(id_val)
        return sorted(missing_ids)

    def get_relations(
        self,
    ) -> dict[
        tuple[tuple[str, str], tuple[str, str]],
        tuple[set[str], dict[str, Any], dict[str, Any]],
    ]:
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
        # main_coll, main_field, back_coll, back_field -> equal_fields, main_field_def, back_field_def
        relations: dict[
            tuple[tuple[str, str], tuple[str, str]],
            tuple[set[str], dict[str, Any], dict[str, Any]],
        ] = {}

        for collection, fields in self.models.items():
            if collection != "_meta":
                for field, field_def in fields.items():
                    if eq := set(field_def.get("equal_fields", [])):
                        if field_def["is_relation"]:
                            back_data = (
                                self.get_generic_back_relation_data(field_def)
                                if field_def["is_generic"]
                                else self.get_non_generic_back_relation_data(field_def)
                            )
                        else:
                            continue
                        for back_collection, back_field_data in back_data.items():
                            for back_field, back_field_def in back_field_data.items():
                                if back_eq := back_field_def.get("equal_fields"):
                                    full_eq = (
                                        {*eq, back_eq}
                                        if isinstance(back_eq, str)
                                        else eq.union(back_eq)
                                    )
                                else:
                                    full_eq = eq
                                if (
                                    collection == "user" or back_collection == "user"
                                ) and "meeting_id" in full_eq:
                                    full_eq.remove("meeting_id")
                                if full_eq and (
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
                                    if collection == "meeting":
                                        relations[
                                            (back_collection, back_field),
                                            (collection, field),
                                        ] = (full_eq, back_field_def, field_def)
                                    else:
                                        relations[
                                            (collection, field),
                                            (back_collection, back_field),
                                        ] = (full_eq, field_def, back_field_def)
        return relations

    def get_non_generic_back_relation_data(
        self, field_def: dict[str, Any]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        back_collection, back_field = list(field_def["to"].items())[0]
        back_field_def = self.models[back_collection][back_field]
        return {back_collection: {back_field: back_field_def}}

    def get_generic_back_relation_data(
        self, field_def: dict[str, Any]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        return {
            coll: {back_field: self.models[coll][back_field]}
            for coll, back_field in field_def["to"].items()
        }

    def is_a_main_relation(
        self,
        coll_a: str,
        field_a: str,
        field_def_a: dict[str, Any],
        coll_b: str,
        field_b: str,
        field_def_b: dict[str, Any],
    ) -> bool:
        generic_a = field_def_a["is_generic"]
        generic_b = field_def_b["is_generic"]
        if generic_a != generic_b:
            return generic_b
        list_a = field_def_a["is_list_relation"]
        list_b = field_def_b["is_list_relation"]
        if list_a != list_b:
            return list_b
        if coll_a == coll_b:
            return field_a <= field_b
        return coll_a < coll_b
