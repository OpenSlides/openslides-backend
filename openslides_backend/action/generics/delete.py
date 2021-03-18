from typing import Any, Dict, Iterable, List, Tuple, Type

from ...models.fields import (
    BaseGenericRelationField,
    BaseTemplateRelationField,
    OnDelete,
)
from ...services.datastore.deleted_models_behaviour import InstanceAdditionalBehaviour
from ...shared.exceptions import ActionException, ProtectedModelsException
from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import FullQualifiedId, transform_to_fqids
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
        # TODO: Check if instance exists in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

        # Update instance (by default this does nothing)
        instance = self.update_instance(instance)

        # Fetch db instance with all relevant fields
        this_fqid = FullQualifiedId(self.model.collection, instance["id"])
        relevant_fields = [
            field.own_field_name
            for field in self.model.get_relation_fields()
            if field.on_delete != OnDelete.SET_NULL
        ]
        db_instance = self.datastore.fetch_model(
            fqid=this_fqid,
            mapped_fields=relevant_fields,
            db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
            lock_result=True,
        )

        # Update instance and set relation fields to None.
        # Gather all delete actions with action data and also all models to be deleted
        delete_actions: List[Tuple[Type[Action], ActionData]] = []
        self.datastore.update_additional_models(this_fqid, DeletedModel())
        for field in self.model.get_relation_fields():
            # Check on_delete.
            if field.on_delete != OnDelete.SET_NULL:
                if isinstance(field, BaseTemplateRelationField):
                    # We currently do not support such template fields.
                    raise NotImplementedError

                # Extract all foreign keys as fqids from the model
                foreign_fqids = db_instance.get(field.own_field_name, [])
                if not isinstance(foreign_fqids, list):
                    foreign_fqids = [foreign_fqids]
                if not isinstance(field, BaseGenericRelationField):
                    assert len(field.to) == 1
                    foreign_fqids = [
                        FullQualifiedId(field.get_target_collection(), id)
                        for id in foreign_fqids
                    ]

                if field.on_delete == OnDelete.PROTECT:
                    protected_fqids = [
                        fqid
                        for fqid in foreign_fqids
                        if not isinstance(
                            self.datastore.additional_relation_models.get(fqid),
                            DeletedModel,
                        )
                    ]
                    if protected_fqids:
                        raise ProtectedModelsException(this_fqid, protected_fqids)
                else:
                    # field.on_delete == OnDelete.CASCADE
                    # Extract all foreign keys as fqids from the model
                    value = db_instance.get(field.own_field_name, [])
                    foreign_fqids = transform_to_fqids(
                        value, field.get_target_collection()
                    )

                    # Execute the delete action for all fqids
                    for fqid in foreign_fqids:
                        if isinstance(
                            self.datastore.additional_relation_models.get(fqid),
                            DeletedModel,
                        ):
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
                        self.datastore.update_additional_models(fqid, DeletedModel())
            else:
                # field.on_delete == OnDelete.SET_NULL
                if isinstance(field, BaseTemplateRelationField):
                    template_field_name = field.get_template_field_name()
                    db_instance = self.datastore.fetch_model(
                        fqid=FullQualifiedId(self.model.collection, instance["id"]),
                        mapped_fields=[template_field_name],
                        lock_result=True,
                        db_additional_relevance=InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
                    )
                    for replacement in db_instance.get(template_field_name, []):
                        structured_field_name = field.get_structured_field_name(
                            replacement
                        )
                        instance[structured_field_name] = None
                else:
                    instance[field.own_field_name] = None

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

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object deleted"
        yield self.build_write_request(EventType.Delete, fqid, information)
