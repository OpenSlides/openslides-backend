from datastore.migrations import BaseModelMigration
from datastore.shared.di import service_as_singleton
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent
from openslides_backend.services.keycloak.interface import IdpAdminService


@service_as_singleton
class Migration(BaseModelMigration):
    """
    This migration removes all default_number fields from user models
    """
    idpAdmin: IdpAdminService

    target_migration_index = 58

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        db_models = self.reader.get_all("user")
        for id_, model in db_models.items():
            if not "kc_id" in model:
                idp_id = self.idpAdmin.create_user(model.get("username"), model.get("password"), model.get("saml_id"))
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("user", id_),
                        {
                            "idp_id": idp_id,
                            "saml_id": None
                        },
                    )
                )
        return events
