from datastore.migrations import BaseEvent, BaseEventMigration, CreateEvent
from datastore.shared.util import collection_from_fqid


class Migration(BaseEventMigration):
    """
    This migration adds some defaults of organization.
    """

    target_migration_index = 10
    collection = "organization"

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        collection = collection_from_fqid(event.fqid)
        if collection == self.collection and isinstance(event, CreateEvent):
            event.data["users_email_sender"] = "OpenSlides"
            event.data["users_email_subject"] = "OpenSlides access data"
            event.data[
                "users_email_body"
            ] = """\
      Dear {name},



      this is your personal OpenSlides login:

          {url}

          username: {username}

          password: {password}



      This email was generated automatically."""
            event.data["url"] = "http://example.com:8000"
            return [event]
        else:
            return None
