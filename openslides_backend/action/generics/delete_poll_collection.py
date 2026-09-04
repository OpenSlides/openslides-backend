from typing import Any, cast

from ...models.base import model_registry
from ...models.fields import BaseGenericRelationField, BaseRelationField, RelationField
from ...shared.exceptions import BadCodingException
from ...shared.filters import FilterOperator
from ...shared.patterns import fqid_from_collection_and_id
from .delete import DeleteAction


class PollCollectionDeleteAction(DeleteAction):
    """
    Generic delete action for collections related to Poll.
    """

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        """Retrieves meeting_id from the related poll."""

        poll_field = self.model.get_field("poll_id")
        if not isinstance(poll_field, RelationField):
            raise BadCodingException(
                "PollCollectionDeleteAction can only be used for collections where poll field has type 'relation'."
            )

        own_id = instance["id"]
        poll_field_name = poll_field.to["poll"]
        reverse_relation_field = cast(
            BaseRelationField, model_registry["poll"]().get_field(poll_field_name)
        )

        db_result = self.datastore.filter(
            collection="poll",
            filter_=FilterOperator(
                field=poll_field_name,
                operator="has" if reverse_relation_field.is_list_field else "=",
                value=(
                    fqid_from_collection_and_id(self.model.collection, own_id)
                    if isinstance(reverse_relation_field, BaseGenericRelationField)
                    else own_id
                ),
            ),
            mapped_fields=["meeting_id"],
            use_changed_models=False,
            lock_result=False,
        )
        return next(iter(db_result.values()))["meeting_id"]
