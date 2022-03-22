from typing import Any, Dict, Iterable, List, Tuple, Type

from ...models.fields import BaseTemplateRelationField, OnDelete
from ...shared.exceptions import ActionException, ProtectedModelsException
from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import Collection, FullQualifiedId, transform_to_fqids
from ...shared.typing import DeletedModel
from ..action import Action
from ..util.actions_map import actions_map
from ..util.typing import ActionData


class DeleteAction(Action):
    """
    Generic delete action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes care of on_delete handling.
        """
        # Update instance (by default this does nothing)
        instance = self.update_instance(instance)

        # Fetch db instance with all relevant fields
        this_fqid = FullQualifiedId(self.model.collection, instance["id"])
        relevant_fields = [
            field.get_own_field_name() for field in self.model.get_relation_fields()
        ] + ["meta_deleted"]
        db_instance = self.datastore.get(
            fqid=this_fqid,
            mapped_fields=relevant_fields,
        )
        # Fetch structured fields in second step
        structured_fields: List[str] = []
        for field in self.model.get_relation_fields():
            if isinstance(field, BaseTemplateRelationField):
                structured_fields += list(
                    self.get_all_structured_fields(field, db_instance)
                )
        if structured_fields:
            db_instance.update(self.datastore.get(this_fqid, structured_fields))

        # Update instance and set relation fields to None.
        # Gather all delete actions with action data and also all models to be deleted
        delete_actions: List[Tuple[Type[Action], ActionData]] = []
        self.datastore.apply_changed_model(this_fqid, DeletedModel())
        for field in self.model.get_relation_fields():
            # Check on_delete.
            if field.on_delete != OnDelete.SET_NULL:
                # Extract all foreign keys as fqids from the model
                foreign_fqids: List[FullQualifiedId] = []
                if isinstance(field, BaseTemplateRelationField):
                    for structured_field_name in self.get_all_structured_fields(
                        field, db_instance
                    ):
                        foreign_fqids += transform_to_fqids(
                            db_instance[structured_field_name],
                            field.get_target_collection(),
                        )
                else:
                    value = db_instance.get(field.get_own_field_name(), [])
                    foreign_fqids = transform_to_fqids(
                        value, field.get_target_collection()
                    )

                if field.on_delete == OnDelete.PROTECT:
                    protected_fqids = [
                        fqid for fqid in foreign_fqids if not self.is_deleted(fqid)
                    ]
                    if protected_fqids:
                        raise ProtectedModelsException(this_fqid, protected_fqids)
                else:
                    # field.on_delete == OnDelete.CASCADE
                    # Execute the delete action for all fqids
                    for fqid in foreign_fqids:
                        if self.is_deleted(fqid):
                            # skip models that are already deleted
                            continue
                        delete_action_class = actions_map.get(
                            f"{str(fqid.collection)}.delete"
                        )
                        if not delete_action_class:
                            raise ActionException(
                                f"Can't cascade the delete action to {str(fqid.collection)} "
                                "since no delete action was found."
                            )
                        # Assume that the delete action uses the standard action data
                        action_data = [{"id": fqid.id}]
                        delete_actions.append((delete_action_class, action_data))
                        self.datastore.apply_changed_model(fqid, DeletedModel())
            else:
                # field.on_delete == OnDelete.SET_NULL
                if isinstance(field, BaseTemplateRelationField):
                    fields = self.get_all_structured_fields(field, db_instance)
                else:
                    fields = [field.get_own_field_name()]

                for field_name in fields:
                    instance[field_name] = None

        # Add additional relation models and execute all previously gathered delete actions
        # catch all protected models exception to gather all protected fqids
        all_protected_fqids: List[FullQualifiedId] = []
        for delete_action_class, delete_action_data in delete_actions:
            try:
                self.execute_other_action(delete_action_class, delete_action_data)
            except ProtectedModelsException as e:
                all_protected_fqids.extend(e.fqids)

        if all_protected_fqids:
            raise ProtectedModelsException(this_fqid, all_protected_fqids)

        return instance

    def get_all_structured_fields(
        self, field: BaseTemplateRelationField, instance: Dict[str, Any]
    ) -> Iterable[str]:
        for replacement in instance.get(field.get_template_field_name(), []):
            yield field.get_structured_field_name(replacement)

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object deleted"
        yield self.build_write_request(EventType.Delete, fqid, information)

    def is_meeting_deleted(self, meeting_id: int) -> bool:
        """
        Returns whether the given meeting was deleted during this request or not.
        """
        return self.datastore.is_deleted(
            FullQualifiedId(Collection("meeting"), meeting_id)
        )

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        return self.datastore.is_deleted(fqid)
